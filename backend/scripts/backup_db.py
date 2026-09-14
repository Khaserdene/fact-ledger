"""SQLite өгөгдлийн санг backups/ хавтас руу аюулгүй хуулна.

sqlite3 backup API ашигладаг тул сервер ажиллаж байх үед ч аюулгүй.
Хэрэглээ:  python scripts/backup_db.py   (backend хавтаснаас)
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Windows консол cp1252 үед кирилл print унагаахаас сэргийлнэ
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BACKEND_DIR / "profiling_facts.db"
BACKUP_DIR = BACKEND_DIR / "backups"
KEEP_LAST = 20  # хамгийн сүүлийн N нөөцийг үлдээнэ


def backup() -> Path:
    if not DB_PATH.exists():
        print(f"DB олдсонгүй: {DB_PATH}")
        sys.exit(1)

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"profiling_facts.{stamp}.db"

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    # Хуучин нөөцүүдийг цэвэрлэх
    backups = sorted(BACKUP_DIR.glob("profiling_facts.*.db"))
    for old in backups[:-KEEP_LAST]:
        old.unlink()

    print(f"Нөөц: {dest}")
    return dest


if __name__ == "__main__":
    backup()
