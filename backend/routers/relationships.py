"""Холбоос endpoint-ууд: гар нэмэх, холбох, татгалзах, устгах."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.dates import parse_flexible_date

router = APIRouter(tags=["relationships"])


@router.post("/relationships", response_model=schemas.RelationshipOut)
def create_relationship(payload: schemas.RelationshipCreate, db: Session = Depends(get_db)):
    """Гар холбоос нэмэх: target нь сонгосон субъект эсвэл чөлөөт нэр."""
    source_entity = db.query(models.Entity).filter(models.Entity.id == payload.source_entity_id).first()
    if not source_entity:
        raise HTTPException(status_code=404, detail="Эх субъект олдсонгүй")

    target_name = (payload.target_name or "").strip()
    target_kind = payload.target_kind
    if payload.target_entity_id is not None:
        target = db.query(models.Entity).filter(models.Entity.id == payload.target_entity_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Зорилтот субъект олдсонгүй")
        if not target_name:
            target_name = target.name
        if not target_kind:
            target_kind = target.entity_type
    elif not target_name:
        raise HTTPException(status_code=400, detail="target_entity_id эсвэл target_name шаардлагатай")

    start_date, start_prec, _ = parse_flexible_date(payload.start_date_input)
    end_date, end_prec, _ = parse_flexible_date(payload.end_date_input)

    rel = models.Relationship(
        source_entity_id=payload.source_entity_id,
        source_id=payload.source_id,
        target_name=target_name,
        target_entity_id=payload.target_entity_id,
        rel_type=payload.rel_type,
        target_kind=target_kind,
        start_date=start_date,
        start_precision=start_prec,
        end_date=end_date,
        end_precision=end_prec,
        source_quote=payload.source_quote,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


@router.post("/relationships/{rel_id}/link")
def link_relationship(rel_id: int, body: schemas.LinkBody, db: Session = Depends(get_db)):
    rel = db.query(models.Relationship).filter(models.Relationship.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Холбоос олдсонгүй")
    target = db.query(models.Entity).filter(models.Entity.id == body.target_entity_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Зорилтот субъект олдсонгүй")
    rel.target_entity_id = body.target_entity_id
    db.commit()
    return {"ok": True}


@router.post("/relationships/{rel_id}/dismiss-link")
def dismiss_relationship_link(rel_id: int, body: schemas.DismissBody, db: Session = Depends(get_db)):
    rel = db.query(models.Relationship).filter(models.Relationship.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Холбоос олдсонгүй")
    dismissed = rel.dismissed_links
    if body.entity_id not in dismissed:
        dismissed.append(body.entity_id)
        rel.dismissed_links = dismissed
        db.commit()
    return {"ok": True}


@router.delete("/relationships/{rel_id}")
def delete_relationship(rel_id: int, db: Session = Depends(get_db)):
    rel = db.query(models.Relationship).filter(models.Relationship.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Холбоос олдсонгүй")
    db.delete(rel)
    db.commit()
    return {"ok": True}
