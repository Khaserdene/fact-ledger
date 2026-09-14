"""Субъект нэгтгэлт: source entity-ийн бүх өгөгдлийг survivor руу шилжүүлж,
source-ийг tombstone (merged_into_id) болгон үлдээнэ."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from services.matching import normalize_name


def merge_entities(db: Session, survivor_id: int, source_id: int) -> schemas.MergeResult:
    if survivor_id == source_id:
        raise HTTPException(status_code=400, detail="Субъектийг өөртэй нь нэгтгэх боломжгүй")

    survivor = db.query(models.Entity).filter(models.Entity.id == survivor_id).first()
    source = db.query(models.Entity).filter(models.Entity.id == source_id).first()
    if not survivor or not source:
        raise HTTPException(status_code=404, detail="Субъект олдсонгүй")
    if survivor.merged_into_id is not None:
        raise HTTPException(status_code=400, detail="Хүлээн авагч субъект өөрөө нэгтгэгдсэн байна")
    if source.merged_into_id is not None:
        raise HTTPException(status_code=400, detail="Энэ субъект аль хэдийн нэгтгэгдсэн байна")

    # Фактууд
    moved_facts = (
        db.query(models.Fact)
        .filter(models.Fact.entity_id == source_id)
        .update({"entity_id": survivor_id}, synchronize_session=False)
    )

    # Холбоосууд (хоёр чиглэлд)
    moved_rels = (
        db.query(models.Relationship)
        .filter(models.Relationship.source_entity_id == source_id)
        .update({"source_entity_id": survivor_id}, synchronize_session=False)
    )
    moved_rels += (
        db.query(models.Relationship)
        .filter(models.Relationship.target_entity_id == source_id)
        .update({"target_entity_id": survivor_id}, synchronize_session=False)
    )
    # Нэгтгэлтийн улмаас үүссэн өөрлүүгээ заасан ирмэгүүдийг устгана
    # (нэгтгэгдсэн хоёр субъектийн хоорондох ирмэг байсан гэсэн үг)
    db.query(models.Relationship).filter(
        models.Relationship.source_entity_id == survivor_id,
        models.Relationship.target_entity_id == survivor_id,
    ).delete(synchronize_session=False)

    # Дурдагдлууд (давхардвал source-ийнхыг хаяна)
    survivor_mention_keys = {
        (m.source_id, m.name_as_written)
        for m in db.query(models.Mention).filter(models.Mention.entity_id == survivor_id).all()
    }
    moved_mentions = 0
    for m in db.query(models.Mention).filter(models.Mention.entity_id == source_id).all():
        if (m.source_id, m.name_as_written) in survivor_mention_keys:
            db.delete(m)
        else:
            m.entity_id = survivor_id
            moved_mentions += 1

    # Alias-ууд: source-ийн alias + source-ийн нэр өөрөө survivor-ийн alias болно
    survivor_norms = {a.alias_norm for a in survivor.aliases}
    survivor_norms.add(normalize_name(survivor.name))
    moved_aliases = 0

    def add_alias(alias_text: str, kind: str | None):
        nonlocal moved_aliases
        norm = normalize_name(alias_text)
        if not norm or norm in survivor_norms:
            return
        survivor_norms.add(norm)
        db.add(models.EntityAlias(
            entity_id=survivor_id, alias=alias_text, alias_norm=norm, kind=kind,
        ))
        moved_aliases += 1

    for a in list(source.aliases):
        add_alias(a.alias, a.kind)
        db.delete(a)
    add_alias(source.name, "merged")

    # Tombstone — bulk update ашиглана (expire_all нь pending ORM
    # өөрчлөлтийг арчдаг тул шууд UPDATE илүү найдвартай)
    db.query(models.Entity).filter(models.Entity.id == source_id).update(
        {"merged_into_id": survivor_id}, synchronize_session=False
    )
    db.commit()

    return schemas.MergeResult(
        survivor_id=survivor_id,
        merged_id=source_id,
        moved_facts=moved_facts,
        moved_relationships=moved_rels,
        moved_aliases=moved_aliases,
        moved_mentions=moved_mentions,
    )
