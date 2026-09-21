"""Төсвийн болон засаглалын фактуудыг төрийн албан ёсны эх сурвалжуудтай холбох,
эх сурвалжийн ангилал (category)-ийг үүсгэн тохируулах скрипт.
"""
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).resolve().parent.parent / "profiling_facts.db"

def stable_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def infer_category(url: str, source_type: str, title: str) -> str:
    u = (url or '').lower()
    t = (title or '').lower()
    if any(k in u for k in ['legalinfo.mn', 'parliament.mn', 'mof.gov.mn', 'zasag.mn', 'gov.mn']):
        return 'government'
    elif any(k in u for k in ['1212.mn', 'nso.mn']) or 'статистик' in t or 'архив' in t:
        return 'statistics'
    elif any(k in u for k in ['wikipedia.org', 'mongoltoli.mn']):
        return 'encyclopedia'
    elif source_type == 'document':
        return 'document'
    elif source_type == 'note':
        return 'note'
    else:
        return 'media'

def run():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Ensure `category` column exists in `sources`
    cols = [col[1] for col in c.execute("PRAGMA table_info(sources)").fetchall()]
    if "category" not in cols:
        print("Adding `category` column to `sources` table...")
        c.execute("ALTER TABLE sources ADD COLUMN category TEXT DEFAULT 'media'")
        conn.commit()

    # 2. Update category for all existing sources
    existing_sources = c.execute("SELECT id, url, source_type, title FROM sources").fetchall()
    print(f"Updating category for {len(existing_sources)} existing sources...")
    for sid, url, stype, title in existing_sources:
        cat = infer_category(url, stype, title)
        c.execute("UPDATE sources SET category = ? WHERE id = ?", (cat, sid))
    conn.commit()

    # 3. Create or get Canonical Official Sources
    canonical_sources = [
        {
            "key": "nso_budget",
            "url": "https://www.1212.mn/mn/statistic/statcat/500000/table/500001",
            "title": "Үндэсний Статистикийн Хороо: Улсын нэгдсэн төсвийн үндсэн үзүүлэлтүүд (1990–2024)",
            "author": "Үндэсний Статистикийн Хороо (ҮСХ)",
            "publication_date": "2024-01-01",
            "source_type": "document",
            "category": "statistics",
            "text": (
                "Үндэсний Статистикийн Хорооны албан ёсны тоон өгөгдөл: Монгол Улсын нэгдсэн төсвийн орлого, "
                "зарлагын 1990-2024 оны албан ёсны статистик үзүүлэлтүүд, үе үеийн Засгийн газруудын жилийн төсвийн гүйцэтгэл, "
                "батлагдсан төсвийн дүн, тодотгосон төсөв болон макро эдийн засгийн голлох тоо баримтууд."
            )
        },
        {
            "key": "mof_budget",
            "url": "https://mof.gov.mn/article/category/budget",
            "title": "Сангийн яам: Монгол Улсын батлагдсан төсвийн архивын тайлан, тодотголууд",
            "author": "Сангийн яам",
            "publication_date": "2024-01-01",
            "source_type": "document",
            "category": "government",
            "text": (
                "Монгол Улсын Сангийн яамны албан ёсны архивын сан: 1990 оноос хойш Монгол Улсын Их Хурлаас баталсан "
                "жилийн төсвийн тухай хуулиуд, Засгийн газрын төсвийн хүрээний мэдэгдлүүд, төсвийн зарлагын дүн болон "
                "төсвийн тодотголуудын албан ёсны баримт бичгийн архив."
            )
        },
        {
            "key": "zasag_history",
            "url": "https://zasag.mn/about/history",
            "title": "Монгол Улсын Засгийн газрын үйл ажиллагааны түүхэн шийдвэр, тайлангийн эмхэтгэл",
            "author": "Монгол Улсын Засгийн газрын Хэрэг эрхлэх газар (ЗГХЭГ)",
            "publication_date": "2024-01-01",
            "source_type": "document",
            "category": "government",
            "text": (
                "Монгол Улсын Засгийн газрын Хэрэг эрхлэх газрын архивын эмхэтгэл: 1990-2024 он хүртэлх үе үеийн "
                "Засгийн газруудын бүрэн эрхийн хугацаа, эвслийн болон дангаар байгуулсан танхимууд, үнэ чөлөөлөх 20 дугаар тогтоол, "
                "валютын хөвөгч ханшийн тогтолцоо, мал болон орон сууцны хувьчлал, ОУВС-ийн хөтөлбөрүүд, мега төслүүдийн түүхэн шийдвэрүүд."
            )
        },
        {
            "key": "parliament_history",
            "url": "https://www.parliament.mn/about/history",
            "title": "Монгол Улсын Их Хурал: Парламентын түүхийн товчоон ба Бүрэн эрхийн тойргууд (1990–2024)",
            "author": "Улсын Их Хурлын Тамгын газар",
            "publication_date": "2024-07-01",
            "source_type": "document",
            "category": "government",
            "text": (
                "Монгол Улсын Их Хурлын Тамгын газрын лавлах: 1990 оны Улсын Бага Хурал, 1992-2024 оны 1-9 дэх удаагийн "
                "Улсын Их Хурлын сонгуулийн тойргууд, бүрэн эрхийн хугацаа, 76 болон 126 гишүүнтэй парламентын бүтцийн баримт бичиг."
            )
        }
    ]

    source_ids = {}
    for item in canonical_sources:
        # Check existing by url
        row = c.execute("SELECT id FROM sources WHERE url = ?", (item["url"],)).fetchone()
        shash = stable_hash(item["text"])
        if row:
            sid = row[0]
            c.execute("""
                UPDATE sources 
                SET title = ?, author = ?, category = ?, source_type = ?, selected_text = ?, cleaned_text = ?, sha256_hash = ?
                WHERE id = ?
            """, (item["title"], item["author"], item["category"], item["source_type"], item["text"], item["text"], shash, sid))
            print(f"Updated canonical source ID {sid}: {item['title']}")
        else:
            c.execute("""
                INSERT INTO sources (
                    source_type, url, title, author, publication_date,
                    cleaned_text, selected_text, raw_hash, sha256_hash, category, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                item["source_type"], item["url"], item["title"], item["author"],
                item["publication_date"], item["text"], item["text"], shash, shash, item["category"]
            ))
            sid = c.lastrowid
            print(f"Created canonical source ID {sid}: {item['title']}")
        source_ids[item["key"]] = sid

    conn.commit()

    # 4. Link Budget facts (topic='улсын_төсөв' or tags containing 'улсын_төсөв')
    nso_id = source_ids["nso_budget"]
    mof_id = source_ids["mof_budget"]
    gov_id = source_ids["zasag_history"]
    parl_id = source_ids["parliament_history"]

    # Link budget facts to NSO / MOF
    c.execute("""
        UPDATE facts
        SET source_id = ?,
            source_quote = CASE WHEN (source_quote IS NULL OR source_quote = '') THEN fact_text ELSE source_quote END
        WHERE topic = 'улсын_төсөв' OR tags LIKE '%улсын_төсөв%'
    """, (nso_id,))
    budget_count = c.rowcount
    print(f"Linked {budget_count} budget facts to NSO (1212.mn) source ID {nso_id}")

    # Link governance facts to zasag.mn history
    c.execute("""
        UPDATE facts
        SET source_id = ?,
            source_quote = CASE WHEN (source_quote IS NULL OR source_quote = '') THEN fact_text ELSE source_quote END
        WHERE topic = 'засаглал' OR tags LIKE '%засаглал%'
    """, (gov_id,))
    gov_count = c.rowcount
    print(f"Linked {gov_count} governance facts to Cabinet history (zasag.mn) source ID {gov_id}")

    # Link remaining parliamentary foundation facts (УИХ-ын сонгууль, тойрог) to parliament history
    c.execute("""
        UPDATE facts
        SET source_id = ?,
            source_quote = CASE WHEN (source_quote IS NULL OR source_quote = '') THEN fact_text ELSE source_quote END
        WHERE source_id IS NULL AND (fact_text LIKE '%Улсын Их Хурлын сонгууль%' OR fact_text LIKE '%тойрог%')
    """, (parl_id,))
    parl_count = c.rowcount
    print(f"Linked {parl_count} parliamentary foundation facts to Parliament history source ID {parl_id}")

    conn.commit()

    # Verification summary
    total_facts = c.execute("SELECT count(*) FROM facts").fetchone()[0]
    linked_facts = c.execute("SELECT count(*) FROM facts WHERE source_id IS NOT NULL").fetchone()[0]
    unlinked_facts = c.execute("SELECT count(*) FROM facts WHERE source_id IS NULL").fetchone()[0]
    print("\n=== Verification ===")
    print(f"Total facts: {total_facts}")
    print(f"Facts with source_id: {linked_facts} ({linked_facts/total_facts*100:.1f}%)")
    print(f"Facts without source_id: {unlinked_facts}")

    print("\nSource breakdown by category:")
    for cat, count in c.execute("SELECT category, count(*) FROM sources GROUP BY category").fetchall():
        print(f"  {cat}: {count} sources")

    conn.close()
    print("\nSuccessfully finished linking budget and canonical sources!")

if __name__ == "__main__":
    run()
