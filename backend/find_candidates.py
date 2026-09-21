import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

def get_members(p_id, p_name):
    rows = c.execute("""
        SELECT DISTINCT e.id, e.name FROM entities e
        LEFT JOIN facts f ON e.id = f.entity_id AND (f.fact_text LIKE ? OR f.role_context LIKE ?)
        LEFT JOIN relationships r ON e.id = r.source_entity_id AND (r.target_entity_id = ? OR r.target_name LIKE ?)
        WHERE e.entity_type = 'person' AND (f.id IS NOT NULL OR r.id IS NOT NULL)
    """, (f"%{p_name}%", f"%{p_name}%", p_id, f"%{p_name}%")).fetchall()
    return {r[1] for r in rows}

# All person entities
all_persons = c.execute("SELECT id, name FROM entities WHERE entity_type='person' AND merged_into_id IS NULL").fetchall()
all_person_names = [p[1] for p in all_persons]

p53 = get_members(53, "УИХ 2016–2020")
p51 = get_members(51, "УИХ 2008–2012")
p55 = get_members(55, "УИХ 2024–2028")

print(f"Entities in DB matching 2016–2020: {len(p53)}/76")
print(f"Entities in DB matching 2008–2012: {len(p51)}/76")
print(f"Entities in DB matching 2024–2028: {len(p55)}/126")

# Check if there are any persons in DB who have 2016, 2008, 2024 in facts but not linked
print("\nChecking candidate persons in DB:")
for pid, pname in all_persons:
    facts = c.execute("SELECT fact_text FROM facts WHERE entity_id=?", (pid,)).fetchall()
    fact_str = " ".join([f[0] for f in facts])
    if "2016" in fact_str and pname not in p53:
        print(f"Candidate for 2016-2020: {pname}")
    if "2008" in fact_str and pname not in p51:
        print(f"Candidate for 2008-2012: {pname}")
    if "2024" in fact_str and pname not in p55:
        print(f"Candidate for 2024-2028: {pname}")
