import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from database import SessionLocal
import models

db = SessionLocal()

gov_entities = db.query(models.Entity).filter(
    (models.Entity.entity_type.in_(["government", "state", "org", "parliament"])) |
    (models.Entity.name.like("%Засгийн газар%")) |
    (models.Entity.name.like("%яам%")) |
    (models.Entity.name.like("%агентлаг%")) |
    (models.Entity.name.like("%газар%"))
).all()

with open("tools/existing_gov_entities.txt", "w", encoding="utf-8") as out:
    out.write(f"Total found: {len(gov_entities)}\n\n")
    for ge in gov_entities:
        out.write(f"[{ge.id}] {ge.name} ({ge.entity_type}) | stub={ge.is_stub}\n")

print("Done writing tools/existing_gov_entities.txt")
db.close()
