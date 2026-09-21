"""Эх сурвалж endpoint-ууд: scrape, нийтлэл/тэмдэглэл/баримт хадгалах, тулгах."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

import models
import schemas
import scraper as scraper_module
import verification
from database import get_db
from hasher import stable_hash

router = APIRouter(tags=["sources"])

SOURCE_TYPES = ("article", "note", "document")


def get_source_or_404(db: Session, source_id: int) -> models.Source:
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Эх сурвалж олдсонгүй")
    return source


def parse_pub_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


@router.post("/scrape", response_model=schemas.ScrapeResponse)
def scrape_url(payload: schemas.ScrapeRequest):
    try:
        result = scraper_module.scrape(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scrape error: {str(e)}")
    return schemas.ScrapeResponse(**result)


def infer_source_category(url: Optional[str], source_type: str, title: str) -> str:
    u = (url or '').lower()
    t = (title or '').lower()
    if any(k in u for k in ['legalinfo.mn', 'parliament.mn', 'mof.gov.mn', 'zasag.mn', 'gov.mn']):
        return 'government'
    elif any(k in u for k in ['1212.mn', 'nso.mn']) or 'статистик' in t or 'архив' in t:
        return 'statistics'
    elif any(k in u for k in ['wikipedia.org', 'mongoltoli.mn']):
        return 'encyclopedia'
    elif source_type == 'document':
        return 'document'
    elif source_type == 'note':
        return 'note'
    else:
        return 'media'


def create_source_from_payload(db: Session, payload: schemas.SourceCreate) -> models.Source:
    if payload.source_type not in SOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Буруу source_type: {payload.source_type}")

    if payload.source_type == "article":
        if not payload.url or not payload.selected_blocks:
            raise HTTPException(status_code=400, detail="Нийтлэлд url + selected_blocks шаардлагатай")
        selected_text = "\n\n".join(payload.selected_blocks)
        cleaned_text = payload.raw_text if payload.raw_text else selected_text
    else:
        if not payload.body or not payload.body.strip():
            raise HTTPException(status_code=400, detail="Тэмдэглэл/баримтад body шаардлагатай")
        selected_text = payload.body.strip()
        cleaned_text = selected_text

    cat = payload.category or infer_source_category(payload.url, payload.source_type, payload.title)

    source = models.Source(
        source_type=payload.source_type,
        category=cat,
        url=payload.url,
        title=payload.title,
        author=payload.author,
        publication_date=parse_pub_date(payload.pub_date),
        cleaned_text=cleaned_text,
        selected_text=selected_text,
        raw_hash=stable_hash(cleaned_text),
        sha256_hash=stable_hash(selected_text),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources", response_model=schemas.SourceOut)
def create_source(payload: schemas.SourceCreate, db: Session = Depends(get_db)):
    return create_source_from_payload(db, payload)


@router.get("/sources", response_model=List[schemas.SourceOut])
def list_sources(
    url: Optional[str] = None,
    source_type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Source)
    if url:
        q = q.filter(models.Source.url == url)
    if source_type:
        q = q.filter(models.Source.source_type == source_type)
    if category and category != "all":
        q = q.filter(models.Source.category == category)
    if search:
        s = f"%{search.strip()}%"
        q = q.filter(
            (models.Source.title.ilike(s)) |
            (models.Source.url.ilike(s)) |
            (models.Source.author.ilike(s))
        )
    return q.order_by(models.Source.created_at.desc()).all()


@router.get("/sources/{source_id}", response_model=schemas.SourceWithFacts)
def get_source(source_id: int, db: Session = Depends(get_db)):
    return get_source_or_404(db, source_id)


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = get_source_or_404(db, source_id)
    # Фактууд эх сурвалжгүй болно (өөрсдөө устахгүй)
    db.query(models.Fact).filter(models.Fact.source_id == source_id).update(
        {"source_id": None}, synchronize_session=False
    )
    db.query(models.Relationship).filter(models.Relationship.source_id == source_id).update(
        {"source_id": None}, synchronize_session=False
    )
    db.query(models.Mention).filter(models.Mention.source_id == source_id).delete(synchronize_session=False)
    db.expire_all()
    db.delete(source)
    db.commit()
    return {"ok": True}


@router.post("/sources/{source_id}/verify", response_model=schemas.VerifyResponse)
def verify_source(source_id: int, db: Session = Depends(get_db)):
    source = get_source_or_404(db, source_id)
    if source.source_type != "article" or not source.url:
        raise HTTPException(status_code=400, detail="Зөвхөн URL-тай нийтлэлийг тулгах боломжтой")
    try:
        result = verification.verify_article(db, source)
        return schemas.VerifyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")


@router.post("/sources/{source_id}/scan-mentions")
def scan_mentions(source_id: int, db: Session = Depends(get_db)):
    """Эх сурвалжийн текстээс одоо буй субъектын нэр/хувилбарыг хайж Mention бүртгэнэ.

    Өмнөх дурдлагуудыг устгаж дахин шалгана (rescan semantics).
    """
    from services.matching import normalize_name

    source = get_source_or_404(db, source_id)
    text = source.selected_text or ""
    norm_text = normalize_name(text)

    db.query(models.Mention).filter(models.Mention.source_id == source.id).delete(synchronize_session=False)

    entities = (
        db.query(models.Entity)
        .options(selectinload(models.Entity.aliases))
        .filter(models.Entity.merged_into_id.is_(None))
        .all()
    )
    created = 0
    for e in entities:
        names = {e.name, *e.alias_list}
        for name in names:
            if len(name.strip()) < 3:
                continue
            if normalize_name(name) in norm_text:
                exists = (
                    db.query(models.Mention)
                    .filter(
                        models.Mention.source_id == source.id,
                        models.Mention.entity_id == e.id,
                        models.Mention.name_as_written == name,
                    )
                    .first()
                )
                if not exists:
                    db.add(models.Mention(
                        source_id=source.id,
                        entity_id=e.id,
                        name_as_written=name,
                    ))
                    created += 1
    db.commit()
    return {"source_id": source.id, "mentions_created": created}
