"""AI JSON import боловсруулалт: факт, холбоос, зөрчлийг давхардал шалгаж хадгална.

Анхаар: Phase 4-т review queue (suggestions) архитектураар солигдоно.
"""
from sqlalchemy.orm import Session

import models
import schemas
from services import contradictions as contradiction_service
from services.dates import parse_flexible_date


def assign_fact_id(db: Session, fact: models.Fact) -> None:
    """flush хийсний дараа PK дээр суурилсан fact_id онооно (collision-гүй)."""
    db.flush()
    fact.fact_id = f"F{fact.id}"


def import_facts(
    db: Session,
    entity: models.Entity,
    payload: schemas.ImportFactsPayload,
) -> schemas.ImportFactsResult:
    entity_id = entity.id
    added = 0
    skipped_dupes = 0
    new_fact_objects: dict[str, models.Fact] = {}

    # Намтрын фактууд
    for item in payload.new_biographical_facts:
        exists = db.query(models.Fact).filter(
            models.Fact.entity_id == entity_id,
            models.Fact.fact_type == "biographical",
            models.Fact.fact_text == item.fact,
        ).first()
        if exists:
            new_fact_objects[item.source_quote or item.fact] = exists
            skipped_dupes += 1
            continue

        fact = models.Fact(
            entity_id=entity_id,
            source_id=payload.article_id,
            fact_type="biographical",
            fact_text=item.fact,
            source_quote=item.source_quote,
            role_context=item.role_context,
        )
        fact.tags = item.tags
        db.add(fact)
        assign_fact_id(db, fact)
        new_fact_objects[item.source_quote or item.fact] = fact
        added += 1

    # Он цагийн фактууд
    for item in payload.new_chronological_facts:
        fact_date, precision, date_end = parse_flexible_date(item.date)

        exists_q = db.query(models.Fact).filter(
            models.Fact.entity_id == entity_id,
            models.Fact.fact_type == "chronological",
            models.Fact.fact_text == item.fact,
        )
        if fact_date:
            exists_q = exists_q.filter(models.Fact.fact_date == fact_date)
        exists = exists_q.first()
        if exists:
            new_fact_objects[item.source_quote or item.fact] = exists
            skipped_dupes += 1
            continue

        fact = models.Fact(
            entity_id=entity_id,
            source_id=payload.article_id,
            fact_type="chronological",
            fact_date=fact_date,
            date_precision=precision,
            fact_date_end=date_end,
            fact_text=item.fact,
            source_quote=item.source_quote,
            role_context=item.role_context,
        )
        fact.tags = item.tags
        db.add(fact)
        assign_fact_id(db, fact)
        new_fact_objects[item.source_quote or item.fact] = fact
        added += 1

    # Холбоосууд (графын ирмэгүүд)
    added_relationships = 0
    for rel in payload.new_relationships:
        rel_start, start_prec, _ = parse_flexible_date(rel.start_date)
        rel_end, end_prec, _ = parse_flexible_date(rel.end_date)
        exists_rel = db.query(models.Relationship).filter(
            models.Relationship.source_entity_id == entity_id,
            models.Relationship.target_name == rel.target_name,
            models.Relationship.rel_type == rel.rel_type,
            models.Relationship.start_date == rel_start,
        ).first()
        if exists_rel:
            continue
        # Субъекттэй холбохыг баталгаажуулах урсгалаар дараа хийнэ, автоматаар биш.
        relationship_obj = models.Relationship(
            source_entity_id=entity_id,
            source_id=payload.article_id,
            target_name=rel.target_name,
            target_entity_id=None,
            rel_type=rel.rel_type,
            target_kind=rel.target_kind,
            start_date=rel_start,
            start_precision=start_prec,
            end_date=rel_end,
            end_precision=end_prec,
            source_quote=rel.source_quote,
        )
        db.add(relationship_obj)
        added_relationships += 1

    # Зөрчлүүд
    saved_contradictions = 0
    skipped = []
    for c in payload.contradictions_detected:
        old_fact = contradiction_service.find_fact_by_fact_id(db, c.contradicted_fact_id)
        if not old_fact:
            skipped.append(c.contradicted_fact_id)
            continue

        new_fact = new_fact_objects.get(c.new_fact_quote)
        if not new_fact:
            new_fact = (
                db.query(models.Fact)
                .filter(
                    models.Fact.entity_id == entity_id,
                    models.Fact.source_quote == c.new_fact_quote,
                )
                .order_by(models.Fact.id.desc())
                .first()
            )
        if not new_fact:
            skipped.append(f"new_fact_quote not found: {c.new_fact_quote[:40]}")
            continue

        contradiction_service.save_contradiction(db, new_fact, old_fact, c.reason)
        saved_contradictions += 1

    db.commit()
    return schemas.ImportFactsResult(
        added_facts=added,
        skipped_duplicates=skipped_dupes,
        added_relationships=added_relationships,
        contradictions_saved=saved_contradictions,
        skipped_contradictions=skipped,
    )
