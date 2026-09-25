# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('backend/profiling_facts.db')
c = conn.cursor()
c.execute("SELECT id, name, entity_type FROM entities WHERE name LIKE '%Ганхуяг%' OR name LIKE '%Аюурсайхан%' OR name LIKE '%Бат-Эрдэнэ%' OR name LIKE '%Эрхэт%' OR name LIKE '%Эрдэнэс%' OR name LIKE '%АТГ%' OR name LIKE '%Авлига%' OR name LIKE '%Хил%'")
print("--- SPECIFIC ENTITIES ---")
c.execute("SELECT id, name, entity_type FROM entities WHERE name LIKE '%Авлигатай%' OR name LIKE '%Эрхэт%' OR name LIKE '%Прокурор%' OR name LIKE '%Тавантолгой%'")
for r in c.fetchall():
    print(r)



