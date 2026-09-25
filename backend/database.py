import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

# .env файлыг ачаалах
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# Орчны хувьсагчаас DATABASE_URL унших (Supabase Postgres эсвэл SQLite)
RAW_DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'profiling_facts.db'}")

# Supabase / Heroku postgres:// -> postgresql:// хөрвүүлэлт (SQLAlchemy 2.0 шаардлага)
if RAW_DB_URL.startswith("postgres://"):
    DATABASE_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = RAW_DB_URL

# SQLite batch migration (Alembic render_as_batch) нэргүй constraint дээр
# унадаг тул бүх constraint-д тогтсон нэр өгнө.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Холболтын тохиргоо (SQLite vs PostgreSQL/Supabase)
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
