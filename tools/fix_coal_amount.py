"""
Нүүрсний хулгайн дүнг 4,400.0B → 6,400.0B ₮ болгон засварлах
Үндэслэл: Эрдэнэс Тавантолгойн аудитын тайлан болон УИХ-ын Түр хорооны баримтаар
тогтоогдсон 6.4 Их наяд ₮ (шууд хохирол + татварын зөрүү + оффтейк алдагдал).
Нийт гэрэгдэгдсэн он: 2018-2022 (гол оффтейк гэрээнүүд 2018-2020 онд байгуулагдаж,
2022 онд хэрэг илэрсэн).
Засгийн газрын хамаарал: cabinet_id=44 (У.Хүрэлсүх, 2017-2021) + cabinet_id=45 (Л.Оюун-Эрдэнэ, 2021-).
Давамгайлах танхим: cabinet_id=44 (оффтейк гэрээнүүд байгуулагдсан үе).
"""
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
db_path = Path("backend/profiling_facts.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Нүүрсний хулгайн засвар
c.execute("""
    UPDATE cases
    SET amount_billion = 6400.0,
        case_year = 2019,
        cabinet_id = 44
    WHERE slug = 'coal-theft'
""")
print(f"coal-theft засварлагдсан: {c.rowcount} мөр")

# Description шинэчлэх
c.execute("""
    UPDATE cases
    SET description = '6.4 их наяд төгрөгийн нүүрсний хулгайн хэрэг: Эрдэнэс Тавантолгойн оффтейк гэрээнүүдийн нууцлал, аудитын зөрүү, бүртгэлгүй гарцын нийт хохирол (УИХ-ын Түр хорооны сонсголын дүгнэлтээр 6.4 их наяд ₮).'
    WHERE slug = 'coal-theft'
""")
print(f"description шинэчлэгдсэн: {c.rowcount} мөр")

conn.commit()

# Шалгах
c.execute("SELECT slug, title, amount_billion, case_year, cabinet_id FROM cases WHERE slug = 'coal-theft'")
r = c.fetchone()
print(f"\nШалгалт:\nSlug: {r[0]}\nДүн: {r[2]} тэрбум ₮ ({r[2]/1000:.1f} Их наяд ₮)\nОн: {r[3]}\nЗасгийн газар ID: {r[4]}")

conn.close()
