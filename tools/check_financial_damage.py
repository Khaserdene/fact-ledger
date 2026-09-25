import os
import sys
import json

sys.path.insert(0, os.path.abspath("backend"))

from database import SessionLocal
import models

db = SessionLocal()

results = {
    "facts_mentioning_damage": [],
    "sources_mentioning_44": [],
    "sources_mentioning_40": [],
    "all_coal_facts_financials": []
}

# 1. Search all facts linked to coal case or in sources >= 139
coal_case = db.query(models.Case).filter(models.Case.slug == "coal-theft").first()
links = db.query(models.CaseLink).filter(models.CaseLink.case_id == coal_case.id).all() if coal_case else []
coal_fact_ids = [l.fact_id for l in links if l.fact_id]

facts = db.query(models.Fact).filter(
    (models.Fact.id.in_(coal_fact_ids)) | (models.Fact.source_id >= 139)
).all()

for f in facts:
    text = (f.fact_text or "") + " " + (f.source_quote or "")
    has_damage = any(w in text.lower() for w in ["их наяд", "тэрбум", "хохирол", "төсөв", "алдагдал", "амнат", "ааноат", "40", "44"])
    if has_damage:
        s = db.query(models.Source).filter(models.Source.id == f.source_id).first()
        results["all_coal_facts_financials"].append({
            "fact_id": f.id,
            "fact_type": f.fact_type,
            "fact_date": str(f.fact_date) if f.fact_date else None,
            "source_id": f.source_id,
            "source_title": s.title if s else None,
            "fact_text": f.fact_text,
            "source_quote": f.source_quote
        })

# 2. Check source texts for 44 and 40
sources = db.query(models.Source).filter(models.Source.id >= 139).all()
for s in sources:
    full_text = s.selected_text or ""
    if "44" in full_text or "44 их наяд" in full_text:
        results["sources_mentioning_44"].append({
            "source_id": s.id,
            "title": s.title,
            "url": s.url
        })
    if "40" in full_text or "40 их наяд" in full_text:
        results["sources_mentioning_40"].append({
            "source_id": s.id,
            "title": s.title,
            "url": s.url
        })

with open("tools/damage_check_result.json", "w", encoding="utf-8") as out:
    json.dump(results, out, ensure_ascii=False, indent=2)

print("Check completed. Results in tools/damage_check_result.json")
