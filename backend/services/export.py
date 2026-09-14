"""Субъектийн экспорт: AI промптод залгах JSON (v2 — F-id, precision огноо)."""
from sqlalchemy.orm import Session

import models
from services.dates import format_flexible_date


def export_entity_json(db: Session, entity: models.Entity) -> dict:
    bio_facts = []
    chron_facts = []
    for f in entity.facts:
        entry = {
            "fact_id": f.fact_id,
            "fact": f.fact_text,
            "source_quote": f.source_quote,
            "role_context": f.role_context or None,
            "tags": f.tags,
        }
        if f.topic:
            entry["topic"] = f.topic
        if f.stance:
            entry["stance"] = f.stance
        if f.fact_type == "biographical":
            bio_facts.append(entry)
        else:
            entry["date"] = format_flexible_date(f.fact_date, f.date_precision, f.fact_date_end)
            chron_facts.append(entry)

    relationships = []
    for r in (
        db.query(models.Relationship)
        .filter(models.Relationship.source_entity_id == entity.id)
        .all()
    ):
        relationships.append({
            "target_name": r.target_name,
            "rel_type": r.rel_type,
            "target_kind": r.target_kind,
            "start_date": format_flexible_date(r.start_date, r.start_precision),
            "end_date": format_flexible_date(r.end_date, r.end_precision),
        })

    return {
        "profile": {
            "primary_name": entity.name,
            "entity_type": entity.entity_type,
            "aliases": entity.alias_list,
            "biographical_facts": bio_facts,
            "chronological_facts": chron_facts,
            "relationships": relationships,
        }
    }
