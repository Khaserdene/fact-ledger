#!/usr/bin/env python3
"""
SQLite -> Supabase (PostgreSQL) Data Migration Tool
FACT LEDGER Intelligence Platform

Ашиглах заавар:
  python tools/migrate_sqlite_to_supabase.py --supabase-url "postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"

эсвэл:
  set DATABASE_URL=postgresql://...
  python tools/migrate_sqlite_to_supabase.py
"""

import argparse
import os
import sys
from pathlib import Path

# Backend хавтсыг path-д нэмэх
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import sqlite3
from sqlalchemy import create_engine, text
from database import Base
import models  # Бүх моделиудыг ачаалах

TABLE_ORDER = [
    "sources",
    "entities",
    "macro_indicators",
    "cases",
    "entity_aliases",
    "macro_datapoints",
    "facts",
    "relationships",
    "mentions",
    "contradictions",
    "case_links",
    "suggestions",
    "extraction_batches",
    "user_sessions",
]


def migrate(sqlite_path: str, supabase_url: str):
    print("=" * 65)
    print("  FACT LEDGER // SQLite -> Supabase PostgreSQL шилжүүлэгч")
    print("=" * 65)

    if not Path(sqlite_path).exists():
        print(f"❌ Алдаа: SQLite файл олдсонгүй: {sqlite_path}")
        sys.exit(1)

    # Postgres URL формат шалгах
    if supabase_url.startswith("postgres://"):
        supabase_url = supabase_url.replace("postgres://", "postgresql://", 1)

    print(f"\n[1/4] SQLite сантай холбогдож байна: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    print(f"[2/4] Supabase PostgreSQL сантай холбогдож байна...")
    pg_engine = create_engine(supabase_url, pool_pre_ping=True)

    # Тест холболт
    with pg_engine.connect() as conn:
        res = conn.execute(text("SELECT version();")).fetchone()
        print(f"   ✅ Холбогдлоо: {res[0][:60]}...")

    print("\n[3/4] Supabase дээр бүх хүснэгтүүдийг (Schema) үүсгэж байна...")
    Base.metadata.create_all(pg_engine)
    print("   ✅ Бүх хүснэгт амжилттай үүсгэгдлээ.")

    print("\n[4/4] Өгөгдлийг хуулж байна...")

    total_migrated = 0

    with pg_engine.begin() as pg_conn:
        # FK шалгалтыг түр суллах (session түвшинд)
        pg_conn.execute(text("SET session_replication_role = 'replica';"))

        for table_name in TABLE_ORDER:
            # SQLite-с шалгах
            sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not sqlite_cur.fetchone():
                continue

            sqlite_cur.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cur.fetchall()
            row_count = len(rows)

            if row_count == 0:
                print(f"   • {table_name:<20}: 0 бичлэг (алгаслаа)")
                continue

            # Хүснэгтийн баганын төрлүүдийг авах
            table_obj = Base.metadata.tables.get(table_name)
            bool_cols = set()
            nullable_typed_cols = set()
            if table_obj is not None:
                for col in table_obj.columns:
                    type_str = str(col.type).upper()
                    if "BOOL" in type_str:
                        bool_cols.add(col.name)
                    if any(t in type_str for t in ("DATE", "TIME", "INT", "FLOAT", "NUMERIC")):
                        nullable_typed_cols.add(col.name)

            # Хуучин өгөгдөл цэвэрлэх
            pg_conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE;'))

            # Багануудын нэрс
            cols = [desc[0] for desc in sqlite_cur.description]
            col_list = ", ".join([f'"{c}"' for c in cols])
            placeholders = ", ".join([f":{c}" for c in cols])

            # Insert
            insert_stmt = text(f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})')
            records = []
            for r in rows:
                d = dict(r)
                for c in bool_cols:
                    if c in d and d[c] is not None:
                        d[c] = bool(d[c])
                for c in nullable_typed_cols:
                    if c in d and d[c] == "":
                        d[c] = None
                records.append(d)

            # Batch insert
            pg_conn.execute(insert_stmt, records)
            total_migrated += row_count
            print(f"   ✅ {table_name:<20}: {row_count:>5} бичлэг хуулагдлаа")

        # Session replication role-ийг буцаах
        pg_conn.execute(text("SET session_replication_role = 'origin';"))

        # PostgreSQL ID sequences-ийг шинэчлэх (дараагийн ID давхцахаас сэргийлэх)
        print("\n[*] PostgreSQL sequence тоолууруудыг синхрончилж байна...")
        for table_name in TABLE_ORDER:
            try:
                pg_conn.execute(text(f"""
                    DO $$
                    DECLARE
                        seq_name text;
                        max_id bigint;
                    BEGIN
                        SELECT pg_get_serial_sequence('"{table_name}"', 'id') INTO seq_name;
                        IF seq_name IS NOT NULL THEN
                            EXECUTE format('SELECT COALESCE(MAX(id), 0) + 1 FROM "%s"', '{table_name}') INTO max_id;
                            EXECUTE format('ALTER SEQUENCE %s RESTART WITH %s', seq_name, max_id);
                        END IF;
                    END $$;
                """))
            except Exception as e:
                pass

    print("\n" + "=" * 65)
    print(f"🎉 ШИЛЖҮҮЛЭГ АМЖИЛТТАЙ ДУУСЛАА! Нийт {total_migrated} бичлэг хуулагдлаа.")
    print("=" * 65)
    print("\nДараагийн алхам:")
    print("1. backend/.env дотор DATABASE_URL-аа Supabase холбоосоор солино.")
    print("2. Програмаа ажиллуулна: start.bat")


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to Supabase PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default=str(BACKEND_DIR / "profiling_facts.db"),
        help="SQLite database file path",
    )
    parser.add_argument(
        "--supabase-url",
        default=os.getenv("DATABASE_URL", ""),
        help="Supabase PostgreSQL connection URI (e.g. postgresql://postgres:[pass]@...)",
    )

    args = parser.parse_args()

    supabase_url = args.supabase_url.strip()
    if not supabase_url:
        print("❌ Алдаа: Supabase PostgreSQL холболтын URI олдсонгүй.")
        print("Хэрэглэх жишээ:")
        print('  python tools/migrate_sqlite_to_supabase.py --supabase-url "postgresql://postgres.xxx:pass@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"')
        print("эсвэл орчны хувьсагчид онооно уу: set DATABASE_URL=postgresql://...")
        sys.exit(1)

    migrate(args.sqlite_path, supabase_url)


if __name__ == "__main__":
    main()
