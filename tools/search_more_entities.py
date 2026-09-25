# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('backend/profiling_facts.db')
c = conn.cursor()

names = [
    "Хүрэлбаатар", "Доржханд", "Энхбаяр", "Ариунболд", "Жаргалсайхан",
    "Дашдаваа", "Удаанжаргал", "Оюутцэцэн", "Ганбат"
]
for n in names:
    c.execute("SELECT id, name, entity_type FROM entities WHERE name LIKE ?", (f"%{n}%",))
    res = c.fetchall()
    print(f"Search '{n}': {res}")
