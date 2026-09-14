"""unified schema: sources, entities+aliases, facts precision, mentions

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-07

Өгөгдөл хадгалагдана:
  - articles → sources (мөрүүд хэвээр)
  - profiles → entities (id хадгалагдана, entity_type='person')
  - profiles.aliases JSON → entity_aliases мөрүүд
  - facts: profile_id→entity_id, article_id→source_id, fact_id='F'||id,
    date_precision heuristic backfill
  - relationships: 0 мөр тул шинэ хэлбэрээр дахин үүсгэнэ
  - contradictions: status='confirmed' default-тэй үлдэнэ
"""
import json
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# services.matching.normalize_name-ийн энэ мөчийн хуулбар (migration нь
# өөрөө бүрэн бие даасан байх ёстой — app код өөрчлөгдөхөд энэ хөдлөхгүй).
_HOMOGLYPHS = str.maketrans({
    "a": "а", "b": "в", "c": "с", "e": "е", "h": "н", "k": "к",
    "m": "м", "o": "о", "p": "р", "t": "т", "x": "х", "y": "у",
})
_PUNCT_RE = re.compile(r"[.\-'\"«»""''‚,]+")
_WS_RE = re.compile(r"\s+")


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    s = name.casefold()
    s = s.translate(_HOMOGLYPHS)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. articles → sources ────────────────────────────────────────────────
    op.rename_table("articles", "sources")
    with op.batch_alter_table("sources") as batch:
        batch.add_column(sa.Column("source_type", sa.Text(), nullable=False, server_default="article"))
        batch.add_column(sa.Column("author", sa.Text(), nullable=True))
        batch.alter_column("url", existing_type=sa.Text(), nullable=True)
    op.execute("DROP INDEX IF EXISTS ix_articles_id")
    op.create_index("ix_sources_id", "sources", ["id"])

    # ── 2. Хоосон хуучин relationships/entities-ийг устгана ─────────────────
    op.drop_table("relationships")
    op.drop_table("entities")

    # ── 3. Нэгдсэн entities ──────────────────────────────────────────────────
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False, server_default="person"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tldr_summary", sa.Text(), nullable=True),
        sa.Column("is_stub", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("merged_into_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_entities"),
        sa.ForeignKeyConstraint(["merged_into_id"], ["entities.id"], name="fk_entities_merged_into_id_entities"),
    )
    op.create_index("ix_entities_id", "entities", ["id"])

    op.execute(
        """
        INSERT INTO entities (id, name, entity_type, description, tldr_summary,
                              is_stub, merged_into_id, created_at, updated_at)
        SELECT id, primary_name, 'person', NULL, tldr_summary, 0, NULL, created_at, created_at
        FROM profiles
        """
    )

    # ── 4. entity_aliases (profiles.aliases JSON задаргаа) ──────────────────
    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("alias_norm", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_entity_aliases"),
        sa.ForeignKeyConstraint(
            ["entity_id"], ["entities.id"],
            name="fk_entity_aliases_entity_id_entities", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("entity_id", "alias_norm", name="uq_entity_aliases_entity_id"),
    )
    op.create_index("ix_entity_aliases_id", "entity_aliases", ["id"])
    op.create_index("ix_entity_aliases_entity_id", "entity_aliases", ["entity_id"])
    op.create_index("ix_entity_aliases_alias_norm", "entity_aliases", ["alias_norm"])

    rows = bind.execute(sa.text("SELECT id, aliases FROM profiles")).fetchall()
    for profile_id, aliases_json in rows:
        try:
            aliases = json.loads(aliases_json or "[]")
        except (ValueError, TypeError):
            aliases = []
        seen_norms = set()
        for alias in aliases:
            alias = (alias or "").strip()
            if not alias:
                continue
            norm = _normalize_name(alias)
            if not norm or norm in seen_norms:
                continue
            seen_norms.add(norm)
            bind.execute(
                sa.text(
                    "INSERT INTO entity_aliases (entity_id, alias, alias_norm, kind, created_at) "
                    "VALUES (:eid, :alias, :norm, NULL, CURRENT_TIMESTAMP)"
                ),
                {"eid": profile_id, "alias": alias, "norm": norm},
            )

    # ── 5. facts дахин барих ─────────────────────────────────────────────────
    op.create_table(
        "facts_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fact_id", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("fact_type", sa.Text(), nullable=False),
        sa.Column("fact_date", sa.Date(), nullable=True),
        sa.Column("date_precision", sa.Text(), nullable=True),
        sa.Column("fact_date_end", sa.Date(), nullable=True),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("role_context", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("stance", sa.Text(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_facts"),
        sa.UniqueConstraint("fact_id", name="uq_facts_fact_id"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], name="fk_facts_entity_id_entities"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_facts_source_id_sources"),
    )
    # date_precision heuristic: 01-01 → year, өдөр=01 → month, бусад → day.
    # (Жинхэнэ 1-р сарын 1 гэсэн факт "year" болно — хүлээн зөвшөөрсөн алдагдал.)
    op.execute(
        """
        INSERT INTO facts_new (id, fact_id, entity_id, source_id, fact_type, fact_date,
                               date_precision, fact_date_end, fact_text, source_quote,
                               role_context, tags, topic, stance, sentiment_score, created_at)
        SELECT id,
               'F' || id,
               profile_id,
               article_id,
               fact_type,
               fact_date,
               CASE
                   WHEN fact_date IS NULL THEN NULL
                   WHEN strftime('%m-%d', fact_date) = '01-01' THEN 'year'
                   WHEN strftime('%d', fact_date) = '01' THEN 'month'
                   ELSE 'day'
               END,
               NULL,
               fact_text,
               source_quote,
               role_context,
               tags,
               NULL,
               NULL,
               sentiment_score,
               created_at
        FROM facts
        """
    )
    op.drop_table("facts")
    op.rename_table("facts_new", "facts")
    op.create_index("ix_facts_id", "facts", ["id"])
    op.create_index("ix_facts_entity_id", "facts", ["entity_id"])

    # ── 6. relationships шинэ хэлбэрээр ──────────────────────────────────────
    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("target_name", sa.Text(), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=True),
        sa.Column("rel_type", sa.Text(), nullable=False),
        sa.Column("target_kind", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("start_precision", sa.Text(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("end_precision", sa.Text(), nullable=True),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("dismissed_links", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_relationships"),
        sa.ForeignKeyConstraint(
            ["source_entity_id"], ["entities.id"], name="fk_relationships_source_entity_id_entities"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_relationships_source_id_sources"),
        sa.ForeignKeyConstraint(
            ["target_entity_id"], ["entities.id"], name="fk_relationships_target_entity_id_entities"
        ),
    )
    op.create_index("ix_relationships_id", "relationships", ["id"])
    op.create_index("ix_relationships_source_entity_id", "relationships", ["source_entity_id"])
    op.create_index("ix_relationships_target_entity_id", "relationships", ["target_entity_id"])

    # ── 7. contradictions: status + resolution_note ──────────────────────────
    with op.batch_alter_table("contradictions") as batch:
        batch.add_column(sa.Column("status", sa.Text(), nullable=False, server_default="confirmed"))
        batch.add_column(sa.Column("resolution_note", sa.Text(), nullable=True))

    # ── 8. mentions ──────────────────────────────────────────────────────────
    op.create_table(
        "mentions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("name_as_written", sa.Text(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_mentions"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_mentions_source_id_sources"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], name="fk_mentions_entity_id_entities"),
        sa.UniqueConstraint("source_id", "entity_id", "name_as_written", name="uq_mentions_source_id"),
    )
    op.create_index("ix_mentions_id", "mentions", ["id"])
    op.create_index("ix_mentions_source_id", "mentions", ["source_id"])
    op.create_index("ix_mentions_entity_id", "mentions", ["entity_id"])

    # ── 9. profiles-ийг устгана ──────────────────────────────────────────────
    op.drop_table("profiles")


def downgrade() -> None:
    raise RuntimeError(
        "0002 downgrade дэмжигдэхгүй — backend/backups/ доторх нөөцөөс сэргээнэ үү."
    )
