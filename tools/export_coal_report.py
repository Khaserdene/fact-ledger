import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from database import SessionLocal
import models

db = SessionLocal()

coal_case = db.query(models.Case).filter(models.Case.slug == "coal-theft").first()
out_data = {
    "case": {
        "id": coal_case.id if coal_case else None,
        "title": coal_case.title if coal_case else None,
        "slug": coal_case.slug if coal_case else None,
        "amount_billion": coal_case.amount_billion if coal_case else None,
        "currency": coal_case.currency if coal_case else None,
        "case_year": coal_case.case_year if coal_case else None,
    },
    "sources": [],
    "case_entities": [],
    "case_facts_count": 0,
    "relationships": []
}

# Find all links to coal case
links = db.query(models.CaseLink).filter(models.CaseLink.case_id == coal_case.id).all() if coal_case else []
entity_links = [l for l in links if l.entity_id]
fact_links = [l for l in links if l.fact_id]
out_data["case_facts_count"] = len(fact_links)

for el in entity_links:
    ent = db.query(models.Entity).filter(models.Entity.id == el.entity_id).first()
    if ent:
        out_data["case_entities"].append({
            "entity_id": ent.id,
            "name": ent.name,
            "entity_type": ent.entity_type,
            "role": el.role,
            "note": el.note
        })

# Sources 139 to 150 (and any earlier coal sources)
sources = db.query(models.Source).filter(models.Source.id >= 139).all()
for s in sources:
    s_facts = db.query(models.Fact).filter(models.Fact.source_id == s.id).all()
    s_obj = {
        "id": s.id,
        "title": s.title,
        "url": s.url,
        "author": s.author,
        "publication_date": str(s.publication_date),
        "facts": []
    }
    for f in s_facts:
        ent = db.query(models.Entity).filter(models.Entity.id == f.entity_id).first()
        s_obj["facts"].append({
            "fact_id": f.id,
            "fact_type": f.fact_type,
            "fact_date": str(f.fact_date) if f.fact_date else None,
            "entity_id": f.entity_id,
            "entity_name": ent.name if ent else None,
            "fact_text": f.fact_text,
            "source_quote": f.source_quote,
            "role_context": f.role_context
        })
    out_data["sources"].append(s_obj)

# Find relationships between entities involved in coal case
coal_entity_ids = [e["entity_id"] for e in out_data["case_entities"]]
# Check if there is a Relationship or EntityRelationship model
# Let's inspect what relationship models exist
for rel_name in ["relationships", "entity_relationships"]:
    pass

with open("tools/coal_report.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print("Saved tools/coal_report.json successfully")
