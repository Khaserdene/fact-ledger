"""Мөрдлөгийн хэрэг / шинжилгээний дэд-граф (Investigation & Case Canvas) endpoint-ууд."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from database import get_db

router = APIRouter(prefix="/cases", tags=["cases"])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.CaseOut])
def list_cases(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Бүх хэргийн жагсаалт."""
    q = db.query(models.Case).options(joinedload(models.Case.links))
    if status:
        q = q.filter(models.Case.status == status)
    if search:
        s = f"%{search.strip()}%"
        q = q.filter(
            (models.Case.title.ilike(s)) | (models.Case.description.ilike(s))
        )
    cases = q.order_by(models.Case.updated_at.desc()).all()
    # Deduplicate from joinedload
    seen = set()
    unique = []
    for c in cases:
        if c.id not in seen:
            seen.add(c.id)
            unique.append(c)
    return unique


@router.post("", response_model=schemas.CaseOut, status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    """Шинэ хэрэг үүсгэх."""
    existing = db.query(models.Case).filter(models.Case.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"'{payload.slug}' slug аль хэдийн бүртгэгдсэн.")
    if payload.status not in models.Case.STATUSES:
        raise HTTPException(status_code=400, detail=f"Буруу status: {payload.status}")
    case = models.Case(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        cover_entity_id=payload.cover_entity_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/{slug}")
def get_case_subgraph(slug: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Хэргийн бүрэн дэд-граф: холбогдох субъектүүд, тэдгээрийн хоорондох
    master relationships, холбогдох фактууд, metadata."""
    case = (
        db.query(models.Case)
        .options(joinedload(models.Case.links))
        .filter(models.Case.slug == slug)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")

    # Case-ийн холбоосуудыг авах
    links = case.links
    entity_ids = [l.entity_id for l in links if l.entity_id is not None]
    fact_ids = [l.fact_id for l in links if l.fact_id is not None]

    # Субъектуудыг авах
    entities = []
    entity_map = {}
    if entity_ids:
        ents = db.query(models.Entity).filter(models.Entity.id.in_(entity_ids)).all()
        for e in ents:
            entity_map[e.id] = e
            entities.append({
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
                "description": e.description,
                "tldr_summary": e.tldr_summary,
            })

    # Фактуудыг авах (case-д шууд холбогдсон)
    facts = []
    if fact_ids:
        fcts = (
            db.query(models.Fact)
            .options(joinedload(models.Fact.source))
            .filter(models.Fact.id.in_(fact_ids))
            .all()
        )
        for f in fcts:
            facts.append({
                "id": f.id,
                "fact_id": f.fact_id,
                "entity_id": f.entity_id,
                "fact_type": f.fact_type,
                "fact_date": str(f.fact_date) if f.fact_date else None,
                "fact_text": f.fact_text,
                "source_quote": f.source_quote,
                "topic": f.topic,
                "tags": f.tags,
                "source_title": f.source_title,
                "source_url": f.source_url,
                "sha256": f.source.sha256_hash if f.source else None,
            })

    # Master relationships (субъектуудын хоорондох — case scope-д шүүнэ)
    edges = []
    if len(entity_ids) >= 2:
        entity_id_set = set(entity_ids)
        rels = (
            db.query(models.Relationship)
            .filter(
                models.Relationship.source_entity_id.in_(entity_ids),
                models.Relationship.target_entity_id.in_(entity_ids),
            )
            .all()
        )
        for r in rels:
            edges.append({
                "id": r.id,
                "source": r.source_entity_id,
                "target": r.target_entity_id,
                "rel_type": r.rel_type,
                "start_date": str(r.start_date) if r.start_date else None,
                "end_date": str(r.end_date) if r.end_date else None,
                "source_quote": r.source_quote,
            })

    # Case links (with canvas coords)
    link_items = []
    for l in links:
        link_items.append({
            "id": l.id,
            "entity_id": l.entity_id,
            "fact_id": l.fact_id,
            "role": l.role,
            "note": l.note,
            "x": l.x,
            "y": l.y,
            "entity_name": entity_map[l.entity_id].name if l.entity_id and l.entity_id in entity_map else None,
            "entity_type": entity_map[l.entity_id].entity_type if l.entity_id and l.entity_id in entity_map else None,
        })

    # Graph nodes: entities + fact nodes + case center node
    graph_nodes = [
        {"id": f"case-{case.id}", "name": case.title, "entity_type": "case", "is_center": True}
    ]
    for e in entities:
        link = next((l for l in links if l.entity_id == e["id"]), None)
        graph_nodes.append({
            "id": e["id"],
            "name": e["name"],
            "entity_type": e["entity_type"],
            "role": link.role if link else "INVOLVED_IN",
            "x": link.x if link else None,
            "y": link.y if link else None,
        })
    for f in facts:
        link = next((l for l in links if l.fact_id == f["id"]), None)
        graph_nodes.append({
            "id": f"fact-{f['id']}",
            "name": (f["fact_text"][:60] + "…") if len(f["fact_text"]) > 60 else f["fact_text"],
            "entity_type": "fact",
            "fact_id": f["id"],
            "role": link.role if link else "EVIDENCE_FOR",
        })

    # Graph edges: case → entities, case → facts, entity ↔ entity (master)
    graph_edges = []
    for l in links:
        target_id = l.entity_id if l.entity_id else f"fact-{l.fact_id}"
        graph_edges.append({
            "source": f"case-{case.id}",
            "target": target_id,
            "rel_type": l.role,
        })
    for e in edges:
        graph_edges.append(e)

    return {
        "case": {
            "id": case.id,
            "slug": case.slug,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "cover_entity_id": case.cover_entity_id,
            "created_at": str(case.created_at),
            "updated_at": str(case.updated_at),
        },
        "graph": {"nodes": graph_nodes, "edges": graph_edges},
        "entities": entities,
        "facts": facts,
        "links": link_items,
        "summary": {
            "entities_count": len(entities),
            "facts_count": len(facts),
            "edges_count": len(edges),
            "links_count": len(link_items),
        },
    }


@router.patch("/{slug}", response_model=schemas.CaseOut)
def update_case(slug: str, payload: schemas.CaseUpdate, db: Session = Depends(get_db)):
    """Хэргийн мэдээлэл засварлах."""
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")
    if payload.title is not None:
        case.title = payload.title
    if payload.description is not None:
        case.description = payload.description
    if payload.status is not None:
        if payload.status not in models.Case.STATUSES:
            raise HTTPException(status_code=400, detail=f"Буруу status: {payload.status}")
        case.status = payload.status
    if payload.cover_entity_id is not None:
        case.cover_entity_id = payload.cover_entity_id
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{slug}", status_code=204)
def delete_case(slug: str, db: Session = Depends(get_db)):
    """Хэрэг устгах (зөвхөн case + links, master data хэвээр)."""
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")
    db.delete(case)
    db.commit()


# ── Links (субъект/факт хэрэгт холбох) ───────────────────────────────────────

@router.post("/{slug}/links", response_model=schemas.CaseLinkOut, status_code=201)
def add_case_link(slug: str, payload: schemas.CaseLinkCreate, db: Session = Depends(get_db)):
    """Субъект эсвэл факт хэрэгт холбох."""
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")
    if not payload.entity_id and not payload.fact_id:
        raise HTTPException(status_code=400, detail="entity_id эсвэл fact_id шаардлагатай.")

    # Давхардал шалгах
    if payload.entity_id:
        existing = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.entity_id == payload.entity_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Субъект аль хэдийн холбогдсон.")
        # Субъект бодитоор байгаа эсэхийг шалгах
        entity = db.query(models.Entity).filter(models.Entity.id == payload.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Субъект олдсонгүй.")

    if payload.fact_id:
        existing = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.fact_id == payload.fact_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Факт аль хэдийн холбогдсон.")
        fact = db.query(models.Fact).filter(models.Fact.id == payload.fact_id).first()
        if not fact:
            raise HTTPException(status_code=404, detail="Факт олдсонгүй.")

    link = models.CaseLink(
        case_id=case.id,
        entity_id=payload.entity_id,
        fact_id=payload.fact_id,
        role=payload.role,
        note=payload.note,
        x=payload.x,
        y=payload.y,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.patch("/{slug}/links/{link_id}", response_model=schemas.CaseLinkOut)
def update_case_link(slug: str, link_id: int, payload: schemas.CaseLinkUpdate, db: Session = Depends(get_db)):
    """Холбоосын role/note/координат шинэчлэх."""
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")
    link = db.query(models.CaseLink).filter(
        models.CaseLink.id == link_id,
        models.CaseLink.case_id == case.id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Холбоос олдсонгүй.")
    if payload.role is not None:
        link.role = payload.role
    if payload.note is not None:
        link.note = payload.note
    if payload.x is not None:
        link.x = payload.x
    if payload.y is not None:
        link.y = payload.y
    db.commit()
    db.refresh(link)
    return link


@router.delete("/{slug}/links/{link_id}", status_code=204)
def remove_case_link(slug: str, link_id: int, db: Session = Depends(get_db)):
    """Холбоос устгах (master data хэвээр)."""
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")
    link = db.query(models.CaseLink).filter(
        models.CaseLink.id == link_id,
        models.CaseLink.case_id == case.id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Холбоос олдсонгүй.")
    db.delete(link)
    db.commit()


# ── Entity Activity (хэргийн хүрээнд субъектийн timeline) ────────────────────

@router.get("/{slug}/entity-activity")
def get_entity_activity(
    slug: str,
    entity_id: Optional[int] = None,
    entityId: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Тухайн хэргийн хүрээнд субъектийн timeline: facts + relationships."""
    target_id = entity_id or entityId
    if not target_id:
        raise HTTPException(status_code=400, detail="entity_id or entityId query parameter is required")
    entity_id = target_id
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Хэрэг олдсонгүй.")

    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Субъект олдсонгүй.")

    # Case-д холбогдсон бүх entity_id-уудыг авах
    case_entity_ids = [
        l.entity_id
        for l in db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.entity_id.isnot(None),
        ).all()
    ]

    # Тухайн субъектийн фактуудыг авах
    facts = (
        db.query(models.Fact)
        .options(joinedload(models.Fact.source))
        .filter(models.Fact.entity_id == entity_id)
        .order_by(models.Fact.fact_date.asc())
        .all()
    )

    timeline = []
    for f in facts:
        timeline.append({
            "id": f.id,
            "type": "fact",
            "fact_id": f.fact_id,
            "fact_type": f.fact_type,
            "date": str(f.fact_date) if f.fact_date else None,
            "text": f.fact_text,
            "source_quote": f.source_quote,
            "topic": f.topic,
            "tags": f.tags,
            "sentiment_score": f.sentiment_score,
            "source_title": f.source_title,
            "source_url": f.source_url,
            "sha256": f.source.sha256_hash if f.source else None,
            "in_case": f.id in [
                l.fact_id for l in db.query(models.CaseLink).filter(
                    models.CaseLink.case_id == case.id,
                    models.CaseLink.fact_id == f.id,
                ).all()
            ],
        })

    # Тухайн субъектийн relationships (case-ийн бусад субъектүүдтэй)
    relationships = []
    if case_entity_ids:
        rels_out = (
            db.query(models.Relationship)
            .filter(
                models.Relationship.source_entity_id == entity_id,
                models.Relationship.target_entity_id.in_(case_entity_ids),
            )
            .all()
        )
        rels_in = (
            db.query(models.Relationship)
            .filter(
                models.Relationship.target_entity_id == entity_id,
                models.Relationship.source_entity_id.in_(case_entity_ids),
            )
            .all()
        )
        for r in rels_out + rels_in:
            relationships.append({
                "id": r.id,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
                "target_name": r.target_name,
                "rel_type": r.rel_type,
                "start_date": str(r.start_date) if r.start_date else None,
                "end_date": str(r.end_date) if r.end_date else None,
                "source_quote": r.source_quote,
            })

    return {
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "description": entity.description,
        },
        "timeline": timeline,
        "relationships": relationships,
        "total_facts": len(timeline),
        "case_linked_facts": len([t for t in timeline if t.get("in_case")]),
    }
