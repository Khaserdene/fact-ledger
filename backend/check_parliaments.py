import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

# 1. Parliaments & expected limits
parliaments = [
    (46, "УИХ 1990–1992 (Шилжилтийн)", 50),
    (47, "УИХ 1992–1996", 76),
    (48, "УИХ 1996–2000", 76),
    (49, "УИХ 2000–2004", 76),
    (50, "УИХ 2004–2008", 76),
    (51, "УИХ 2008–2012", 76),
    (52, "УИХ 2012–2016", 76),
    (53, "УИХ 2016–2020", 76),
    (54, "УИХ 2020–2024", 76),
    (55, "УИХ 2024–2028", 126),
]

print("=== УИХ-ЫН СУБЪЕКТҮҮДИЙН ГИШҮҮДИЙН БҮРДЭЛ (НАРИЙВЧИЛСАН) ===\n")

for p_id, p_name, exp in parliaments:
    # Fetch distinct members
    members = c.execute("""
        SELECT DISTINCT e.id, e.name FROM entities e
        LEFT JOIN facts f ON e.id = f.entity_id AND (f.fact_text LIKE ? OR f.role_context LIKE ?)
        LEFT JOIN relationships r ON e.id = r.source_entity_id AND (r.target_entity_id = ? OR r.target_name LIKE ?)
        WHERE e.entity_type = 'person' AND (f.id IS NOT NULL OR r.id IS NOT NULL)
    """, (f"%{p_name}%", f"%{p_name}%", p_id, f"%{p_name}%")).fetchall()

    actual = len(members)
    missing = exp - actual

    if missing > 0:
        print(f"⚠️ [ID: {p_id}] {p_name}")
        print(f"   • Хууль ёсны гишүүдийн тоо: {exp}")
        print(f"   • Системд бүртгэгдсэн гишүүн: {actual}")
        print(f"   • Дутуу гишүүний тоо: {missing} гишүүн дутуу")
        print(f"   • Бүртгэгдсэн гишүүдийн жишээ: {', '.join([m[1] for m in members[:5]]) if members else 'Бүртгэгдсэн гишүүн байхгүй'}\n")
    else:
        print(f"✅ [ID: {p_id}] {p_name} — Бүрэлдэхүүн БҮРЭН ({actual}/{exp})\n")
