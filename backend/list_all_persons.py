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

p53_names = get_members(53, "УИХ 2016–2020")
p51_names = get_members(51, "УИХ 2008–2012")
p55_names = get_members(55, "УИХ 2024–2028")

print(f"Total 2016-2020: {len(p53_names)}")
print(f"Total 2008-2012: {len(p51_names)}")
print(f"Total 2024-2028: {len(p55_names)}")

# Let's check which entities with facts mentioning UIKH 2016-2020 or similar are not in p53_names
all_entities = c.execute("SELECT id, name FROM entities WHERE entity_type='person' AND merged_into_id IS NULL").fetchall()

print("\n--- ALL PERSONS IN DB ---")
print(f"Total person entities: {len(all_entities)}")
