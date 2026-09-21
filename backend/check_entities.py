import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

entities = c.execute('''
    SELECT e.id, e.name, e.entity_type, e.description, e.tldr_summary, e.is_stub,
           COUNT(f.id) as fact_count,
           SUM(CASE WHEN f.fact_type = 'biographical' THEN 1 ELSE 0 END) as bio_count,
           SUM(CASE WHEN f.fact_type = 'chronological' THEN 1 ELSE 0 END) as chrono_count
    FROM entities e
    LEFT JOIN facts f ON e.id = f.entity_id
    WHERE e.merged_into_id IS NULL
    GROUP BY e.id
''').fetchall()

print(f"TOTAL ENTITIES: {len(entities)}")

categories = {
    'no_facts': [],
    'low_facts': [],
    'missing_bio_or_chrono': [],
    'missing_desc_or_tldr': []
}

for ent in entities:
    e_id, name, etype, desc, tldr, is_stub, f_count, bio_c, chrono_c = ent
    bio_c = bio_c or 0
    chrono_c = chrono_c or 0

    item = {
        'id': e_id,
        'name': name,
        'type': etype,
        'f_count': f_count,
        'bio': bio_c,
        'chrono': chrono_c,
        'has_desc': bool(desc and len(desc.strip()) > 5),
        'has_tldr': bool(tldr and len(tldr.strip()) > 5)
    }

    if f_count == 0:
        categories['no_facts'].append(item)
    elif f_count < 3:
        categories['low_facts'].append(item)
    elif bio_c == 0 or chrono_c == 0:
        categories['missing_bio_or_chrono'].append(item)
    
    if not item['has_desc'] or not item['has_tldr']:
        categories['missing_desc_or_tldr'].append(item)

print(f"1. No Facts: {len(categories['no_facts'])}")
print(f"2. Low Facts (<3): {len(categories['low_facts'])}")
print(f"3. Missing Bio or Chrono (when facts >= 3): {len(categories['missing_bio_or_chrono'])}")
print(f"4. Missing Desc or TLDR (Total): {len(categories['missing_desc_or_tldr'])}")

print("\n--- SAMPLE LOW FACTS ---")
for x in categories['low_facts']:
    print(f"• ID: {x['id']} | {x['name']} ({x['type']}) | Facts: {x['f_count']} (Bio:{x['bio']}, Chrono:{x['chrono']})")

print("\n--- SAMPLE MISSING BIO OR CHRONO ---")
for x in categories['missing_bio_or_chrono']:
    print(f"• ID: {x['id']} | {x['name']} ({x['type']}) | Facts: {x['f_count']} (Bio:{x['bio']}, Chrono:{x['chrono']})")
