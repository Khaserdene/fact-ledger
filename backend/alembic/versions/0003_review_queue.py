"""review queue: extraction_batches + suggestions

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),  # extraction | sweep_fuzzy | sweep_ai
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=False),  # manual | gemini | claude | system
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="awaiting_response"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_extraction_batches"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], name="fk_extraction_batches_entity_id_entities"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_extraction_batches_source_id_sources"),
    )
    op.create_index("ix_extraction_batches_id", "extraction_batches", ["id"])
    op.create_index("ix_extraction_batches_status", "extraction_batches", ["status"])

    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),  # fact|relationship|entity|contradiction|merge|link|alias
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),  # JSON
        sa.Column("dedup_status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("dedup_ref_id", sa.Integer(), nullable=True),
        sa.Column("dedup_score", sa.Float(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("edited", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("accepted_kind", sa.Text(), nullable=True),
        sa.Column("accepted_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_suggestions"),
        sa.ForeignKeyConstraint(["batch_id"], ["extraction_batches.id"], name="fk_suggestions_batch_id_extraction_batches"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], name="fk_suggestions_entity_id_entities"),
    )
    op.create_index("ix_suggestions_id", "suggestions", ["id"])
    op.create_index("ix_suggestions_batch_id", "suggestions", ["batch_id"])
    op.create_index("ix_suggestions_status", "suggestions", ["status"])


def downgrade() -> None:
    op.drop_table("suggestions")
    op.drop_table("extraction_batches")
