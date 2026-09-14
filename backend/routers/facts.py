"""Факт endpoint-ууд: гар оруулга, засвар, устгах, sentiment."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.dates import parse_flexible_date
from services.importing import assign_fact_id

router = APIRouter(tags=["facts"])

FACT_TYPES = ("biographical", "chronological")


def get_fact_or_404(db: Session, fact_id: int) -> models.Fact:
    fact = db.query(models.Fact).filter(models.Fact.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Факт олдсонгүй")
    return fact


def validate_sentiment(score):
    if score is not None and not (-1.0 <= float(score) <= 1.0):
        raise HTTPException(status_code=400, detail="sentiment_score нь -1.0 … 1.0 хооронд байх ёстой")


@router.post("/facts", response_model=schemas.FactOut)
def create_fact(payload: schemas.FactCreate, db: Session = Depends(get_db)):
    """Гар факт оруулга."""
    if payload.fact_type not in FACT_TYPES:
        raise HTTPException(status_code=400, detail=f"Буруу fact_type: {payload.fact_type}")
    entity = db.query(models.Entity).filter(models.Entity.id == payload.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Субъект олдсонгүй")
    if payload.source_id is not None:
        source = db.query(models.Source).filter(models.Source.id == payload.source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Эх сурвалж олдсонгүй")
    validate_sentiment(payload.sentiment_score)

    fact_date, precision, date_end = parse_flexible_date(payload.date_input)
    fact = models.Fact(
        entity_id=payload.entity_id,
        source_id=payload.source_id,
        fact_type=payload.fact_type,
        fact_date=fact_date,
        date_precision=precision,
        fact_date_end=date_end,
        fact_text=payload.fact_text,
        source_quote=payload.source_quote,
        role_context=payload.role_context,
        topic=payload.topic,
        stance=payload.stance,
        sentiment_score=payload.sentiment_score,
    )
    fact.tags = payload.tags
    db.add(fact)
    assign_fact_id(db, fact)
    db.commit()
    db.refresh(fact)
    return fact


@router.get("/facts/{fact_id}", response_model=schemas.FactOut)
def get_fact(fact_id: int, db: Session = Depends(get_db)):
    return get_fact_or_404(db, fact_id)


@router.patch("/facts/{fact_id}", response_model=schemas.FactOut)
def update_fact(fact_id: int, payload: schemas.FactUpdate, db: Session = Depends(get_db)):
    fact = get_fact_or_404(db, fact_id)
    data = payload.model_dump(exclude_unset=True)

    if "fact_type" in data:
        if data["fact_type"] not in FACT_TYPES:
            raise HTTPException(status_code=400, detail=f"Буруу fact_type: {data['fact_type']}")
        fact.fact_type = data["fact_type"]
    if "fact_text" in data:
        fact.fact_text = data["fact_text"]
    if "date_input" in data:
        fact.fact_date, fact.date_precision, fact.fact_date_end = parse_flexible_date(data["date_input"])
    if "source_id" in data:
        fact.source_id = data["source_id"]
    if "source_quote" in data:
        fact.source_quote = data["source_quote"]
    if "role_context" in data:
        fact.role_context = data["role_context"]
    if "tags" in data and data["tags"] is not None:
        fact.tags = data["tags"]
    if "topic" in data:
        fact.topic = data["topic"]
    if "stance" in data:
        fact.stance = data["stance"]
    if "sentiment_score" in data:
        validate_sentiment(data["sentiment_score"])
        fact.sentiment_score = data["sentiment_score"]

    db.commit()
    db.refresh(fact)
    return fact


@router.delete("/facts/{fact_id}")
def delete_fact(fact_id: int, db: Session = Depends(get_db)):
    fact = get_fact_or_404(db, fact_id)
    # Эхлээд холбогдсон зөрчлүүдийг устгана
    db.query(models.Contradiction).filter(
        (models.Contradiction.new_fact_id == fact_id) |
        (models.Contradiction.contradicted_fact_id == fact_id)
    ).delete(synchronize_session=False)
    db.expire_all()
    db.delete(fact)
    db.commit()
    return {"ok": True}


@router.patch("/facts/{fact_id}/sentiment")
def update_fact_sentiment(fact_id: int, body: dict, db: Session = Depends(get_db)):
    """Фактын sentiment оноог тохируулна. Хязгаар: -1.0 … 1.0."""
    fact = get_fact_or_404(db, fact_id)
    score = body.get("sentiment_score")
    validate_sentiment(score)
    fact.sentiment_score = float(score) if score is not None else None
    db.commit()
    return {"ok": True, "fact_id": fact_id, "sentiment_score": fact.sentiment_score}
