import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('backend/profiling_facts.db')
c = conn.cursor()

print("--- CASES TABLE ---")
c.execute("SELECT id, slug, title, amount_billion, case_year, cabinet_id FROM cases")
for r in c.fetchall():
    print(f"ID: {r[0]}, Slug: {r[1]}, Amount: {r[3]}B, Year: {r[4]}, Cabinet: {r[5]}")

print("\n--- TABLES ---")
tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(tables)

print("\n--- CASE COAL-THEFT DETAILS ---")
c.execute("SELECT id, slug, title, description FROM cases WHERE slug='coal-theft'")
print(c.fetchall())

print("\n--- CASE LINKS / FACTS RELATED TO COAL ---")
c.execute("""
    SELECT f.id, f.fact_text, f.fact_type 
    FROM facts f 
    WHERE f.fact_text LIKE '%нүүрс%' OR f.fact_text LIKE '%ЭТТ%' OR f.fact_text LIKE '%44%' OR f.fact_text LIKE '%их наяд%'
    LIMIT 20
""")
for r in c.fetchall():
    print(f"[{r[0]}] [{r[2]}] {r[1][:150]}...")

