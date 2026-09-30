import sys
import io
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import Case, CaseLink, Entity, Fact

db = SessionLocal()
cases = db.query(Case).order_by(Case.id).all()
print(f"Нийт {len(cases)} хэрэг олдлоо.\n")

for c in cases:
    entities = [(l.entity.name, l.role) for l in c.links if l.entity]
    facts = [(l.fact.id, l.fact.fact_text, l.fact.fact_date, l.fact.sentiment_score) for l in c.links if l.fact]
    
    print(f"=== [ID: {c.id}] {c.title} ({c.slug}) ===")
    print(f"Ангилал: {c.category} | Төлөв: {c.status} | Он: {c.case_year} | Дүн: {c.amount_billion} {c.currency}")
    print(f"Одоогийн тайлбар: {c.description}")
    print(f"Холбогдох субъектүүд ({len(entities)}):")
    for name, role in entities:
        print(f"  - {name} [{role}]")
    print(f"Холбогдох баримтууд/фактууд ({len(facts)}):")
    for fid, ftext, fdate, sent in facts:
        print(f"  * [F{fid} | {fdate}] {ftext[:120]}... (sent: {sent})")
    print("\n" + "="*70 + "\n")
