"""Субъект (нэгдсэн entity) endpoint-ууд: CRUD, merge, alias, факт, холбоос."""
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

import models
import schemas
from database import get_db
from services import export as export_service
from services import importing
from services import merge as merge_service
from services.matching import normalize_name

router = APIRouter(tags=["entities"])


def get_entity_or_404(db: Session, entity_id: int) -> models.Entity:
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Субъект олдсонгүй")
    return entity


def entity_names(entity: models.Entity) -> set[str]:
    return {entity.name, *entity.alias_list}


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/entities", response_model=List[schemas.EntityOut])
def list_entities(
    q: Optional[str] = None,
    entity_type: Optional[str] = None,
    include_stubs: bool = True,
    include_merged: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(models.Entity).options(selectinload(models.Entity.aliases))
    if not include_merged:
        query = query.filter(models.Entity.merged_into_id.is_(None))
    if not include_stubs:
        query = query.filter(models.Entity.is_stub.is_(False))
    if entity_type:
        query = query.filter(models.Entity.entity_type == entity_type)
    if q:
        alias_match = (
            db.query(models.EntityAlias.entity_id)
            .filter(models.EntityAlias.alias_norm.contains(normalize_name(q)))
        )
        query = query.filter(or_(
            models.Entity.name.contains(q),
            models.Entity.id.in_(alias_match),
        ))
    result = query.order_by(models.Entity.name).all()

    # Намын холбоо: person → party relationships-ээс нэр бүрд тогтооно
    parties = db.query(models.Entity).filter(models.Entity.entity_type == "party").all()
    party_ids = [p.id for p in parties]
    party_names = {p.id: p.name for p in parties}
    party_map: Dict[int, str] = {}
    if party_ids:
        rels = (
            db.query(models.Relationship)
            .filter(models.Relationship.target_entity_id.in_(party_ids))
            .order_by(models.Relationship.id)
            .all()
        )
        for r in rels:
            party_map.setdefault(r.source_entity_id, party_names.get(r.target_entity_id, ""))
    for e in result:
        if e.entity_type == "party":
            e.party_name = e.name
        else:
            e.party_name = party_map.get(e.id) or None
    return result


@router.post("/entities", response_model=schemas.EntityOut)
def create_entity(payload: schemas.EntityCreate, db: Session = Depends(get_db)):
    if payload.entity_type not in models.Entity.TYPES:
        raise HTTPException(status_code=400, detail=f"Буруу entity_type: {payload.entity_type}")
    entity = models.Entity(
        name=payload.name.strip(),
        entity_type=payload.entity_type,
        description=payload.description,
    )
    db.add(entity)
    db.flush()
    _add_aliases(db, entity, payload.aliases)
    db.commit()
    db.refresh(entity)
    return entity


def _add_aliases(db: Session, entity: models.Entity, aliases: List[str], kind: Optional[str] = None) -> int:
    existing_norms = {a.alias_norm for a in entity.aliases}
    existing_norms.add(normalize_name(entity.name))
    added = 0
    for alias in aliases:
        alias = (alias or "").strip()
        norm = normalize_name(alias)
        if not alias or not norm or norm in existing_norms:
            continue
        existing_norms.add(norm)
        db.add(models.EntityAlias(entity_id=entity.id, alias=alias, alias_norm=norm, kind=kind))
        added += 1
    return added


@router.get("/entities/{entity_id}", response_model=schemas.EntityOut)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    return get_entity_or_404(db, entity_id)


@router.patch("/entities/{entity_id}", response_model=schemas.EntityOut)
def update_entity(entity_id: int, payload: schemas.EntityUpdate, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    if payload.name is not None:
        entity.name = payload.name.strip()
    if payload.entity_type is not None:
        if payload.entity_type not in models.Entity.TYPES:
            raise HTTPException(status_code=400, detail=f"Буруу entity_type: {payload.entity_type}")
        entity.entity_type = payload.entity_type
    if payload.description is not None:
        entity.description = payload.description
    if payload.tldr_summary is not None:
        entity.tldr_summary = payload.tldr_summary
    if payload.is_stub is not None:
        entity.is_stub = payload.is_stub
    db.commit()
    db.refresh(entity)
    return entity


@router.delete("/entities/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    fact_ids = [f.id for f in entity.facts]
    if fact_ids:
        db.query(models.Contradiction).filter(
            (models.Contradiction.new_fact_id.in_(fact_ids)) |
            (models.Contradiction.contradicted_fact_id.in_(fact_ids))
        ).delete(synchronize_session=False)
        db.query(models.Fact).filter(models.Fact.entity_id == entity_id).delete(synchronize_session=False)
    db.query(models.Relationship).filter(
        models.Relationship.source_entity_id == entity_id
    ).delete(synchronize_session=False)
    db.query(models.Relationship).filter(
        models.Relationship.target_entity_id == entity_id
    ).update({"target_entity_id": None}, synchronize_session=False)
    db.query(models.Mention).filter(models.Mention.entity_id == entity_id).delete(synchronize_session=False)
    # Энэ рүү заасан tombstone-уудыг чөлөөлнө
    db.query(models.Entity).filter(models.Entity.merged_into_id == entity_id).update(
        {"merged_into_id": None}, synchronize_session=False
    )
    db.expire_all()
    db.delete(entity)
    db.commit()
    return {"ok": True}


# ── Merge ────────────────────────────────────────────────────────────────────

@router.post("/entities/{entity_id}/merge", response_model=schemas.MergeResult)
def merge_into_entity(entity_id: int, body: schemas.MergeRequest, db: Session = Depends(get_db)):
    """body.source_entity_id субъектийг {entity_id} руу нэгтгэнэ."""
    return merge_service.merge_entities(db, survivor_id=entity_id, source_id=body.source_entity_id)


# ── Aliases ──────────────────────────────────────────────────────────────────

@router.post("/entities/{entity_id}/aliases", response_model=schemas.EntityOut)
def add_alias(entity_id: int, body: schemas.AliasCreate, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    added = _add_aliases(db, entity, [body.alias], kind=body.kind)
    if not added:
        raise HTTPException(status_code=409, detail="Ийм нэрийн хувилбар аль хэдийн байна")
    db.commit()
    db.refresh(entity)
    return entity


@router.delete("/entities/{entity_id}/aliases/{alias_id}", response_model=schemas.EntityOut)
def delete_alias(entity_id: int, alias_id: int, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    alias = db.query(models.EntityAlias).filter(
        models.EntityAlias.id == alias_id,
        models.EntityAlias.entity_id == entity_id,
    ).first()
    if not alias:
        raise HTTPException(status_code=404, detail="Нэрийн хувилбар олдсонгүй")
    db.delete(alias)
    db.commit()
    db.refresh(entity)
    return entity


# ── Facts / summary / flags ──────────────────────────────────────────────────

@router.get("/entities/{entity_id}/facts", response_model=List[schemas.FactOut])
def get_entity_facts(entity_id: int, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    return entity.facts


def build_summary(entity: models.Entity) -> Dict[str, Any]:
    total_facts = len(entity.facts)
    bio_count = sum(1 for f in entity.facts if f.fact_type == "biographical")
    chron_count = sum(1 for f in entity.facts if f.fact_type == "chronological")
    red_flags = sum(1 for f in entity.facts if f.sentiment_score is not None and f.sentiment_score < -0.3)
    green_flags = sum(1 for f in entity.facts if f.sentiment_score is not None and f.sentiment_score > 0.3)

    all_tags: dict = {}
    for fact in entity.facts:
        for tag in fact.tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1
    top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "entity_id": entity.id,
        "name": entity.name,
        "entity_type": entity.entity_type,
        "tldr_summary": entity.tldr_summary,
        "stats": {
            "total_facts": total_facts,
            "biographical_facts": bio_count,
            "chronological_facts": chron_count,
            "red_flags": red_flags,
            "green_flags": green_flags,
        },
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
    }


@router.get("/entities/{entity_id}/summary")
def get_entity_summary(entity_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    entity = get_entity_or_404(db, entity_id)
    return build_summary(entity)


def build_flags(entity: models.Entity) -> Dict[str, Any]:
    red_facts, green_facts, neutral_facts = [], [], []
    for fact in entity.facts:
        entry = {
            "id": fact.id,
            "fact_text": fact.fact_text,
            "fact_date": fact.fact_date.isoformat() if fact.fact_date else None,
            "tags": fact.tags,
            "sentiment_score": fact.sentiment_score,
        }
        if fact.sentiment_score is not None:
            if fact.sentiment_score < -0.3:
                red_facts.append(entry)
            elif fact.sentiment_score > 0.3:
                green_facts.append(entry)
            else:
                neutral_facts.append(entry)
        else:
            neutral_facts.append(entry)

    return {
        "entity_id": entity.id,
        "red_flags": sorted(red_facts, key=lambda x: x["sentiment_score"] or 0),
        "green_flags": sorted(green_facts, key=lambda x: x["sentiment_score"] or 0, reverse=True),
        "neutral": neutral_facts,
    }


@router.get("/entities/{entity_id}/flags")
def get_entity_flags(entity_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    entity = get_entity_or_404(db, entity_id)
    return build_flags(entity)


@router.delete("/entities/{entity_id}/facts")
def clear_entity_facts(entity_id: int, db: Session = Depends(get_db)):
    """Субъектийн бүх факт (болон зөрчил)-ийг устгана, субъект хэвээр үлдэнэ."""
    entity = get_entity_or_404(db, entity_id)
    fact_ids = [f.id for f in entity.facts]
    if fact_ids:
        db.query(models.Contradiction).filter(
            (models.Contradiction.new_fact_id.in_(fact_ids)) |
            (models.Contradiction.contradicted_fact_id.in_(fact_ids))
        ).delete(synchronize_session=False)
        db.query(models.Fact).filter(models.Fact.entity_id == entity_id).delete(synchronize_session=False)
    db.query(models.Relationship).filter(
        models.Relationship.source_entity_id == entity_id
    ).delete(synchronize_session=False)
    db.expire_all()
    db.commit()
    return {"deleted": len(fact_ids)}


# ── Relationships (субъектийн харагдац) ──────────────────────────────────────

@router.get("/entities/{entity_id}/relationships", response_model=List[schemas.RelationshipOut])
def get_entity_relationships(entity_id: int, db: Session = Depends(get_db)):
    get_entity_or_404(db, entity_id)
    return (
        db.query(models.Relationship)
        .filter(models.Relationship.source_entity_id == entity_id)
        .order_by(models.Relationship.start_date)
        .all()
    )


def build_candidate(r: models.Relationship) -> schemas.RelationshipCandidate:
    return schemas.RelationshipCandidate(
        id=r.id,
        source_entity_id=r.source_entity_id,
        source_entity_name=r.source_entity.name if r.source_entity else "?",
        target_name=r.target_name,
        rel_type=r.rel_type,
        target_kind=r.target_kind,
        start_date=r.start_date,
        end_date=r.end_date,
        source_quote=r.source_quote,
        source_id=r.source_id,
    )


@router.get("/entities/{entity_id}/relationship-candidates", response_model=List[schemas.RelationshipCandidate])
def relationship_candidates(entity_id: int, db: Session = Depends(get_db)):
    """target_name нь энэ субъектийн нэр/alias-тай таарч буй, холбогдоогүй ирмэгүүд."""
    entity = get_entity_or_404(db, entity_id)
    names = entity_names(entity)
    rels = (
        db.query(models.Relationship)
        .filter(
            models.Relationship.target_entity_id.is_(None),
            models.Relationship.source_entity_id != entity_id,  # өөрөө өөртөө холбогдохгүй
        )
        .all()
    )
    return [
        build_candidate(r)
        for r in rels
        if r.target_name in names and entity_id not in r.dismissed_links
    ]


@router.get("/entities/{entity_id}/relationships-incoming", response_model=List[schemas.RelationshipCandidate])
def incoming_relationships(entity_id: int, db: Session = Depends(get_db)):
    """Бусад субъектээс энэ субъект руу заасан баталгаажсан ирмэгүүд."""
    get_entity_or_404(db, entity_id)
    rels = (
        db.query(models.Relationship)
        .filter(models.Relationship.target_entity_id == entity_id)
        .order_by(models.Relationship.start_date)
        .all()
    )
    return [build_candidate(r) for r in rels]


# ── Export / import ──────────────────────────────────────────────────────────

@router.get("/entities/{entity_id}/export-json")
def export_entity_json(entity_id: int, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    return export_service.export_entity_json(db, entity)


@router.post("/entities/{entity_id}/import-facts", response_model=schemas.ImportFactsResult)
def import_facts(entity_id: int, payload: schemas.ImportFactsPayload, db: Session = Depends(get_db)):
    entity = get_entity_or_404(db, entity_id)
    return importing.import_facts(db, entity, payload)


# ── Knowledge graph ──────────────────────────────────────────────────────────

@router.get("/graph")
def knowledge_graph(db: Session = Depends(get_db)):
    """Нүүр хуудасны knowledge graph-ийн бүх node ба ирмэг.

    Ghost node: target_entity_id-гүй ирмэгүүд (зөвхөн target_name) —
    id нь "g:{relationship_id}" хэлбэртэй, хажуудаас холбогдохгүй.
    """
    entities = (
        db.query(models.Entity)
        .options(selectinload(models.Entity.aliases))
        .filter(models.Entity.merged_into_id.is_(None))
        .all()
    )
    rels = db.query(models.Relationship).all()

    fact_counts: Dict[int, int] = {}
    contradiction_entity_ids: set = set()
    facts = db.query(models.Fact).all()
    fact_by_id = {f.id: f for f in facts}
    contradictions = (
        db.query(models.Contradiction)
        .filter(models.Contradiction.status == "confirmed")
        .all()
    )
    for c in contradictions:
        for f in (fact_by_id.get(c.new_fact_id), fact_by_id.get(c.contradicted_fact_id)):
            if f:
                contradiction_entity_ids.add(f.entity_id)
    for f in facts:
        fact_counts[f.entity_id] = fact_counts.get(f.entity_id, 0) + 1

    entity_ids = {e.id for e in entities}

    # Node бүрийн идэвхийн хугацаа: фактын огноо + холбоосын огнооны хамгийн бага/их
    active: Dict[int, list] = defaultdict(list)

    def track(entity_id, *dates):
        for d in dates:
            if d:
                active[entity_id].append(d)

    for f in facts:
        track(f.entity_id, f.fact_date, f.fact_date_end)
    for r in rels:
        track(r.source_entity_id, r.start_date, r.end_date)
        if r.target_entity_id:
            track(r.target_entity_id, r.start_date, r.end_date)

    nodes = []
    for e in entities:
        dates = active.get(e.id) or []
        nodes.append({
            "id": str(e.id),
            "name": e.name,
            "entity_type": e.entity_type,
            "is_stub": e.is_stub,
            "tldr_summary": e.tldr_summary,
            "description": e.description,
            "aliases": e.alias_list,
            "fact_count": fact_counts.get(e.id, 0),
            "has_contradiction": e.id in contradiction_entity_ids,
            "active_from": min(dates).isoformat() if dates else None,
            "active_to": max(dates).isoformat() if dates else None,
        })

    edges = []
    for r in rels:
        if r.source_entity_id not in entity_ids:
            continue
        edge = {
            "id": r.id,
            "source": str(r.source_entity_id),
            "target": str(r.target_entity_id) if r.target_entity_id in entity_ids else None,
            "target_name": r.target_name,
            "rel_type": r.rel_type,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
        }
        if edge["target"] is None:
            ghost_id = f"g:{r.id}"
            edge["target"] = ghost_id
            g_dates = [d for d in (r.start_date, r.end_date) if d]
            nodes.append({
                "id": ghost_id,
                "name": r.target_name,
                "entity_type": r.target_kind or "other",
                "is_stub": True,
                "tldr_summary": None,
                "description": None,
                "aliases": [],
                "fact_count": 0,
                "has_contradiction": False,
                "active_from": min(g_dates).isoformat() if g_dates else None,
                "active_to": max(g_dates).isoformat() if g_dates else None,
                "ghost": True,
            })
        edges.append(edge)

    # ЗГ ↔ УИХ тойрог: бүрэн эрхийн хугацаа давхцаж буйг шууд холбоос болгох —
    # ингэснээр force layout ЗГ болон тухайн үеийн УИХ-ын гишүүдийг ойрхон бүлэглэнэ
    gov_nodes = {n["id"]: n for n in nodes if n["entity_type"] == "government"}
    parl_nodes = {n["id"]: n for n in nodes if n["entity_type"] == "parliament"}

    def years(n, key):
        v = n.get(key)
        return int(v[:4]) if v else None

    next_edge_id = max((e["id"] for e in edges), default=0) + 1
    for gid_node in gov_nodes.values():
        g_from, g_to = years(gid_node, "active_from"), years(gid_node, "active_to")
        if g_from is None:
            continue
        for pid_node in parl_nodes.values():
            p_from, p_to = years(pid_node, "active_from"), years(pid_node, "active_to")
            if p_from is None:
                continue
            if p_from <= (g_to or p_to) and (p_to or p_from) >= g_from:
                edges.append({
                    "id": f"gp:{gid_node}-{pid_node}",
                    "source": gid_node,
                    "target": pid_node,
                    "rel_type": "бүрэн эрхийн хугацаа",
                    "start_date": None,
                    "end_date": None,
                })
                next_edge_id += 1

    return {"nodes": nodes, "edges": edges}
