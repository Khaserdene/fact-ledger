import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

# 1. 2016-2020 (ID: 53, Target count: 76)
# Missing 2: Эрдэнэбатын Жарлаг (Ж.Эрдэнэбат), ...
mps_2016 = [
    "Жаргалтулгын Эрдэнэбат", # Ж.Эрдэнэбат (Ерөнхий сайд, УИХ-ын гишүүн 2016-2020)
    "Ням-Осорын Учрал"       # Н.Учрал (УИХ-ын гишүүн 2016-2020)
]

# 2. 2008-2012 (ID: 51, Target count: 76)
# Missing 4:
mps_2008 = [
    "Цахиагийн Элбэгдорж",     # Ц.Элбэгдорж (2008 онд УИХ-ын гишүүнээр сонгогдсон)
    "Ухнаагийн Хүрэлсүх",     # У.Хүрэлсүх (2008-2012 онд УИХ-ын гишүүн)
    "Мэндсайханы Энхсайхан",   # М.Энхсайхан (2008-2012 онд УИХ-ын гишүүн)
    "Жамбын Батсуурь"         # Ж.Батсуурь (2008-2012 онд УИХ-ын гишүүн)
]

# 3. 2024-2028 (ID: 55, Target count: 126)
# Missing 7:
mps_2024 = [
    "Ухнаагийн Отгонбаяр",
    "Дашдэмбэрэлийн Бат-Эрдэнэ",
    "Жамбын Батсуурь",
    "Ширнэнбандийн Адъшаа",
    "Сандагийн Бямбацогт",
    "Лхагвын Мөнхбаатар",
    "Лувсанцэрэнгийн Энх-Амгалан"
]

added_facts = 0
added_rels = 0

def add_mp_to_parliament(person_name, parl_id, parl_name, date_str):
    global added_facts, added_rels
    
    # 1. Find or get entity_id
    res = c.execute("SELECT id FROM entities WHERE name=? AND merged_into_id IS NULL", (person_name,)).fetchone()
    if not res:
        # Create entity if not exists
        c.execute("INSERT INTO entities (name, entity_type, is_stub) VALUES (?, 'person', 0)", (person_name,))
        person_id = c.lastrowid
        print(f"[NEW ENTITY] Created person: {person_name} (ID: {person_id})")
    else:
        person_id = res[0]

    # 2. Check if relationship already exists
    rel_exists = c.execute("""
        SELECT id FROM relationships 
        WHERE source_entity_id=? AND (target_entity_id=? OR target_name=?)
    """, (person_id, parl_id, parl_name)).fetchone()

    if not rel_exists:
        c.execute("""
            INSERT INTO relationships (source_entity_id, target_name, target_entity_id, rel_type, target_kind)
            VALUES (?, ?, ?, 'гишүүн', 'parliament')
        """, (person_id, parl_name, parl_id))
        added_rels += 1

    # 3. Check if fact already exists
    fact_text = f"{person_name} нь {parl_name}-ын гишүүнээр сонгогдон ажилласан."
    fact_exists = c.execute("""
        SELECT id FROM facts WHERE entity_id=? AND fact_text=?
    """, (person_id, fact_text)).fetchone()

    if not fact_exists:
        c.execute("""
            INSERT INTO facts (entity_id, fact_type, fact_date, date_precision, fact_text, role_context)
            VALUES (?, 'chronological', ?, 'year', ?, ?)
        """, (person_id, date_str, fact_text, f"{parl_name}-ын гишүүн"))
        added_facts += 1

print("--- ADDING MISSING MPS TO PARLIAMENTS (53, 51, 55) ---")

for mp in mps_2016:
    add_mp_to_parliament(mp, 53, "УИХ 2016–2020", "2016-07-01")

for mp in mps_2008:
    add_mp_to_parliament(mp, 51, "УИХ 2008–2012", "2008-07-01")

for mp in mps_2024:
    add_mp_to_parliament(mp, 55, "УИХ 2024–2028", "2024-07-01")

conn.commit()
print(f"\nSuccessfully added {added_rels} relationships and {added_facts} facts.")
