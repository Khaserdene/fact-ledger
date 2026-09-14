"""Зөрчлийн endpoint-ууд."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(tags=["contradictions"])


@router.get("/contradictions", response_model=List[schemas.ContradictionOut])
def list_contradictions(
    entity_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Contradiction)
    if entity_id:
        q = q.join(models.Fact, models.Contradiction.new_fact_id == models.Fact.id).filter(
            models.Fact.entity_id == entity_id
        )
    if status:
        q = q.filter(models.Contradiction.status == status)
    return q.order_by(models.Contradiction.created_at.desc()).all()


@router.patch("/contradictions/{contradiction_id}", response_model=schemas.ContradictionOut)
def update_contradiction(
    contradiction_id: int,
    payload: schemas.ContradictionUpdate,
    db: Session = Depends(get_db),
):
    c = db.query(models.Contradiction).filter(models.Contradiction.id == contradiction_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Зөрчил олдсонгүй")
    if payload.status is not None:
        if payload.status not in models.Contradiction.STATUSES:
            raise HTTPException(status_code=400, detail=f"Буруу status: {payload.status}")
        c.status = payload.status
    if payload.resolution_note is not None:
        c.resolution_note = payload.resolution_note
    db.commit()
    db.refresh(c)
    return c
