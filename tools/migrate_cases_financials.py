import sqlite3
from pathlib import Path

db_path = Path("backend/profiling_facts.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
cols = [r[1] for r in c.execute("PRAGMA table_info(cases)").fetchall()]
print("Existing cases columns:", cols)

fields = [
    ("amount_billion", "REAL"),
    ("currency", "TEXT DEFAULT 'MNT'"),
    ("case_year", "INTEGER"),
    ("cabinet_id", "INTEGER"),
]

for col_name, col_type in fields:
    if col_name not in cols:
        print(f"Adding {col_name}...")
        c.execute(f"ALTER TABLE cases ADD COLUMN {col_name} {col_type}")

conn.commit()
print("Updated cases columns:", [r[1] for r in c.execute("PRAGMA table_info(cases)").fetchall()])
conn.close()
