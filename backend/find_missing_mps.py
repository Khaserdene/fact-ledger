import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

# All person entities in DB
all_persons = c.execute("SELECT id, name FROM entities WHERE entity_type='person' AND merged_into_id IS NULL").fetchall()

def get_existing_members(p_id, p_name):
    members = c.execute("""
        SELECT DISTINCT e.id, e.name FROM entities e
        LEFT JOIN facts f ON e.id = f.entity_id AND (f.fact_text LIKE ? OR f.role_context LIKE ?)
        LEFT JOIN relationships r ON e.id = r.source_entity_id AND (r.target_entity_id = ? OR r.target_name LIKE ?)
        WHERE e.entity_type = 'person' AND (f.id IS NOT NULL OR r.id IS NOT NULL)
    """, (f"%{p_name}%", f"%{p_name}%", p_id, f"%{p_name}%")).fetchall()
    return {m[1] for m in members}

p53_existing = get_existing_members(53, "УИХ 2016–2020")
p51_existing = get_existing_members(51, "УИХ 2008–2012")
p55_existing = get_existing_members(55, "УИХ 2024–2028")

print(f"УИХ 2016–2020 current count: {len(p53_existing)}")
print(f"УИХ 2008–2012 current count: {len(p51_existing)}")
print(f"УИХ 2024–2028 current count: {len(p55_existing)}")
