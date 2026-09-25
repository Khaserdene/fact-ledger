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
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Бүх хэргийн жагсаалт."""
    q = db.query(models.Case).options(joinedload(models.Case.links))
    if status:
        q = q.filter(models.Case.status == status)
    if category:
        q = q.filter(models.Case.category == category)
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
        category=payload.category or "scandal",
        status=payload.status,
        cover_entity_id=payload.cover_entity_id,
        amount_billion=payload.amount_billion,
        currency=payload.currency or "MNT",
        case_year=payload.case_year,
        cabinet_id=payload.cabinet_id,
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
                "source_id": f.source_id,
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
                "is_master_rel": True,
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
        # Субъектийн хэрэг дэх хамгийн эхний огноо
        first_date = None
        for f in facts:
            if f.get("entity_id") == e["id"] and f.get("fact_date"):
                if not first_date or f["fact_date"] < first_date:
                    first_date = f["fact_date"]
        graph_nodes.append({
            "id": e["id"],
            "name": e["name"],
            "entity_type": e["entity_type"],
            "role": link.role if link else "INVOLVED_IN",
            "first_date": first_date,
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
            "date": f.get("fact_date"),
            "role": link.role if link else "EVIDENCE_FOR",
        })

    # Graph edges: case → entities, case → facts, entity ↔ entity (master), fact → entity
    graph_edges = []
    for l in links:
        target_id = l.entity_id if l.entity_id else f"fact-{l.fact_id}"
        graph_edges.append({
            "source": f"case-{case.id}",
            "target": target_id,
            "rel_type": l.role,
        })
    # Холбогдох субъект рүү фактын ирмэг татах (fact node → entity node)
    for f in facts:
        if f.get("entity_id") and f["entity_id"] in entity_ids:
            graph_edges.append({
                "source": f["entity_id"],
                "target": f"fact-{f['id']}",
                "rel_type": "нотлох_баримт",
                "is_fact_edge": True,
            })
    for e in edges:
        graph_edges.append(e)

    return {
        "case": {
            "id": case.id,
            "slug": case.slug,
            "title": case.title,
            "description": case.description,
            "category": case.category or "scandal",
            "status": case.status,
            "cover_entity_id": case.cover_entity_id,
            "amount_billion": case.amount_billion,
            "currency": case.currency,
            "case_year": case.case_year,
            "cabinet_id": case.cabinet_id,
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
    if payload.category is not None:
        case.category = payload.category
    if payload.status is not None:
        if payload.status not in models.Case.STATUSES:
            raise HTTPException(status_code=400, detail=f"Буруу status: {payload.status}")
        case.status = payload.status
    if payload.cover_entity_id is not None:
        case.cover_entity_id = payload.cover_entity_id
    if payload.amount_billion is not None:
        case.amount_billion = payload.amount_billion
    if payload.currency is not None:
        case.currency = payload.currency
    if payload.case_year is not None:
        case.case_year = payload.case_year
    if payload.cabinet_id is not None:
        case.cabinet_id = payload.cabinet_id
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
            "source_id": f.source_id,
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


# ── Сүлжээний огтлолцол ба Бүлэглэл илрүүлэлт ──────────────────────────────

@router.get("/network/cross-case-analysis")
def get_cross_case_network_analysis(
    min_cases: int = 2,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Олон хэрэг дамнан холбогдсон зангилаа субъектүүд болон картель/бүлэглэлийн огтлолцлыг шинжлэх."""
    # 1. Олон хэрэгт нэр холбогдсон субъектүүд
    entity_cases = (
        db.query(
            models.Entity.id,
            models.Entity.name,
            models.Entity.entity_type,
            func.count(func.distinct(models.CaseLink.case_id)).label("case_count"),
            func.group_concat(func.distinct(models.Case.title)).label("case_titles"),
            func.group_concat(func.distinct(models.Case.slug)).label("case_slugs"),
        )
        .join(models.CaseLink, models.CaseLink.entity_id == models.Entity.id)
        .join(models.Case, models.CaseLink.case_id == models.Case.id)
        .group_by(models.Entity.id, models.Entity.name, models.Entity.entity_type)
        .having(func.count(func.distinct(models.CaseLink.case_id)) >= min_cases)
        .order_by(func.count(func.distinct(models.CaseLink.case_id)).desc())
        .all()
    )

    top_entities = [
        {
            "id": r[0],
            "name": r[1],
            "entity_type": r[2],
            "case_count": r[3],
            "case_titles": r[4].split(",") if r[4] else [],
            "case_slugs": r[5].split(",") if r[5] else [],
        }
        for r in entity_cases
    ]

    # 2. Хамтын оролцоотой хосууд (Pairwise Co-occurrence)
    cl1 = models.CaseLink
    cl2 = models.CaseLink
    co_occurrences = (
        db.query(
            models.CaseLink.entity_id.label("e1_id"),
            models.Entity.name.label("e1_name"),
            models.CaseLink.case_id,
        )
        .join(models.Entity, models.CaseLink.entity_id == models.Entity.id)
        .filter(models.CaseLink.entity_id.isnot(None))
        .all()
    )

    # Calculate shared cases between entity pairs
    entity_to_cases = {}
    entity_names = {}
    for row in co_occurrences:
        entity_to_cases.setdefault(row.e1_id, set()).add(row.case_id)
        entity_names[row.e1_id] = row.e1_name

    cases_dict = {c.id: c.title for c in db.query(models.Case).all()}

    shared_pairs = []
    e_ids = list(entity_to_cases.keys())
    for i in range(len(e_ids)):
        for j in range(i + 1, len(e_ids)):
            id1, id2 = e_ids[i], e_ids[j]
            shared = entity_to_cases[id1].intersection(entity_to_cases[id2])
            if len(shared) >= min_cases:
                shared_pairs.append({
                    "entity_1": {"id": id1, "name": entity_names[id1]},
                    "entity_2": {"id": id2, "name": entity_names[id2]},
                    "shared_count": len(shared),
                    "cases": [cases_dict.get(cid, str(cid)) for cid in shared],
                })

    shared_pairs.sort(key=lambda x: x["shared_count"], reverse=True)

    # 3. Улс төрч/Компани ↔ 29 Хэрэг бүрийн бүрэн матриц (Heatmap Matrix)
    all_cases = db.query(models.Case).order_by(models.Case.id.asc()).all()
    all_links = (
        db.query(models.CaseLink)
        .options(joinedload(models.CaseLink.entity))
        .filter(models.CaseLink.entity_id.isnot(None))
        .all()
    )

    # entity_id -> {case_id -> role}
    entity_case_roles = {}
    for l in all_links:
        if l.entity_id:
            entity_case_roles.setdefault(l.entity_id, {})[l.case_id] = {
                "role": l.role,
                "note": l.note,
            }

    # Матрицад харуулах гол субъектүүд (дор хаяж 1 хэрэгт холбогдсон)
    # Эрэмбэлэлт: хамгийн олон хэрэгт холбогдсоноор нь
    matrix_entities = []
    for ent_id, c_dict in sorted(entity_case_roles.items(), key=lambda x: len(x[1]), reverse=True):
        ent = entities.get(ent_id) if 'entities' in locals() else db.query(models.Entity).filter(models.Entity.id == ent_id).first()
        if not ent:
            continue
        matrix_entities.append({
            "id": ent.id,
            "name": ent.name,
            "entity_type": ent.entity_type,
            "case_count": len(c_dict),
            "cases": {
                str(cid): c_dict[cid] for cid in c_dict
            }
        })

    cases_summary = [
        {
            "id": c.id,
            "slug": c.slug,
            "title": c.title,
            "category": c.category,
            "status": c.status,
            "amount_billion": c.amount_billion,
            "currency": c.currency,
            "case_year": c.case_year,
            "cabinet_id": c.cabinet_id,
            "links_count": len(c.links)
        }
        for c in all_cases
    ]

    # 4. Худалдан авалт, Оффтейк, Картель / Сэжигтэй түншлэлийн шинжилгээ (Procurement Cartels)
    # Зээл, тендер, гэрээ, оффтейк, хамаарал бүхий компани, удирдлагуудын зангилаа
    procurement_cartels = []
    company_rels = (
        db.query(models.Relationship)
        .options(
            joinedload(models.Relationship.source_entity),
            joinedload(models.Relationship.target_entity),
        )
        .all()
    )

    for r in company_rels:
        s_ent = r.source_entity
        t_ent = r.target_entity
        if not s_ent or not t_ent:
            continue
        # Компани эсвэл сан, төрийн байгууллага, гүйцэтгэх удирдлагын холбоос
        s_type = s_ent.entity_type
        t_type = t_ent.entity_type
        is_corporate_nexus = (
            s_type in ("company", "fund", "org") or 
            t_type in ("company", "fund", "org") or
            any(k in r.rel_type.lower() for k in ["гүйцэтгэх", "захирал", "хувьцаа", "зээлдэгч", "оффтейк", "түнш", "эзэмшигч", "хамаарал"])
        )
        if not is_corporate_nexus:
            continue

        # Холбогдсон хэргүүд
        s_cases = set(entity_to_cases.get(s_ent.id, []))
        t_cases = set(entity_to_cases.get(t_ent.id, []))
        shared = s_cases.intersection(t_cases)

        # Эрсдэлийн оноо (Risk Score)
        risk_score = 40
        if shared:
            risk_score += len(shared) * 25
        if any(w in r.rel_type.lower() for k in ["оффтейк", "чанаргүй", "зээл", "хамаарал"] for w in [k]):
            risk_score += 20

        risk_score = min(98, risk_score)

        procurement_cartels.append({
            "id": r.id,
            "source_entity": {"id": s_ent.id, "name": s_ent.name, "type": s_ent.entity_type},
            "target_entity": {"id": t_ent.id, "name": t_ent.name, "type": t_ent.entity_type},
            "rel_type": r.rel_type,
            "source_quote": r.source_quote,
            "shared_cases": [cases_dict.get(cid, str(cid)) for cid in shared],
            "shared_cases_count": len(shared),
            "risk_score": risk_score,
        })

    procurement_cartels.sort(key=lambda x: (x["shared_cases_count"], x["risk_score"]), reverse=True)

    return {
        "min_cases_threshold": min_cases,
        "key_hub_entities_count": len(top_entities),
        "key_hub_entities": top_entities,
        "shared_case_pairs": shared_pairs,
        "cases_summary": cases_summary,
        "matrix_entities": matrix_entities[:60], # Топ 60 гол холбогдогчийн матриц
        "procurement_cartels": procurement_cartels[:40], # Сэжигтэй төсөв/тендер/оффтейк зангилаанууд
    }
