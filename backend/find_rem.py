import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

def get_members(p_id, p_name):
    rows = c.execute("""
        SELECT DISTINCT e.name FROM entities e
        LEFT JOIN facts f ON e.id = f.entity_id AND (f.fact_text LIKE ? OR f.role_context LIKE ?)
        LEFT JOIN relationships r ON e.id = r.source_entity_id AND (r.target_entity_id = ? OR r.target_name LIKE ?)
        WHERE e.entity_type = 'person' AND (f.id IS NOT NULL OR r.id IS NOT NULL)
    """, (f"%{p_name}%", f"%{p_name}%", p_id, f"%{p_name}%")).fetchall()
    return {r[0] for r in rows}

p53 = get_members(53, "УИХ 2016–2020")
p55 = get_members(55, "УИХ 2024–2028")

print(f"p53: {len(p53)}/76")
print(f"p55: {len(p55)}/126")

# Check if there are other MP entities in DB not linked to 53 or 55
all_persons = [p[0] for p in c.execute("SELECT name FROM entities WHERE entity_type='person' AND merged_into_id IS NULL").fetchall()]

print("\nPersons in DB not in 2016-2020 (53):")
for name in all_persons:
    if name not in p53:
        facts = c.execute("SELECT fact_text FROM facts f JOIN entities e ON f.entity_id=e.id WHERE e.name=?", (name,)).fetchall()
        f_text = " ".join([f[0] for f in facts])
        if "2016" in f_text or "УИХ" in f_text or "гишүүн" in f_text:
            print(f"  - {name} | facts: {f_text[:100]}")

print("\nPersons in DB not in 2024-2028 (55):")
for name in all_persons:
    if name not in p55:
        facts = c.execute("SELECT fact_text FROM facts f JOIN entities e ON f.entity_id=e.id WHERE e.name=?", (name,)).fetchall()
        f_text = " ".join([f[0] for f in facts])
        if "2024" in f_text or "УИХ" in f_text or "гишүүн" in f_text:
            print(f"  - {name} | facts: {f_text[:100]}")
