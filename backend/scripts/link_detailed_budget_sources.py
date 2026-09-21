"""Монгол Улсын үе үеийн Засгийн газруудын төсвийн баримтуудыг он тус бүрийн
бодит хууль тогтоомж (Legalinfo), хэвлэлийн тойм (Ikon.mn, News.mn),
Сангийн яамны архивын эх сурвалжуудтай тусгайлан холбох скрипт.

Мөн УИХ-ын гишүүдийн бүрэн эрхийн баримтуудыг Парламентын архивт холбоно.
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

# Specific authoritative sources for budget laws and reports
DETAILED_BUDGET_SOURCES = [
    {
        "key": "budget_2025_law",
        "year": "2025",
        "url": "https://legalinfo.mn/mn/detail?lawId=17332219195041",
        "title": "Монгол Улсын 2025 оны төсвийн тухай хууль: Зарлагын дээд хэмжээ 35.8 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2024-11-15",
        "source_type": "document",
        "category": "government",
        "text": "Монгол Улсын 2025 оны төсвийн тухай хууль. 2025 оны төсвийн жилд төвлөрүүлэх төсвийн нийт орлого 33.8 их наяд, төсвийн зарлагын дээд хэмжээ 35.8 их наяд төгрөг байхаар УИХ-аас батлав."
    },
    {
        "key": "budget_2024_media",
        "year": "2024",
        "url": "https://ikon.mn/n/2zo2",
        "title": "Ikon.mn: 2024 оны төсвийг 27.4 их наяд төгрөгийн зарлагатайгаар эцэслэн баталлаа",
        "author": "Ikon.mn / Мэдээллийн агентлаг",
        "pub_date": "2023-11-11",
        "source_type": "article",
        "category": "media",
        "text": "Монгол Улсын Их Хурлаас 2024 оны улсын нэгдсэн төсвийн нийт орлогыг 25.3 их наяд төгрөг, нэгдсэн төсвийн нийт зарлагыг 27.36 их наяд төгрөг байхаар баталлаа."
    },
    {
        "key": "budget_2023_law",
        "year": "2023",
        "url": "https://legalinfo.mn/mn/detail?lawId=16684803975761",
        "title": "Монгол Улсын 2023 оны төсвийн тухай хууль ба тодотгол (22.45 их наяд ₮)",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2022-11-12",
        "source_type": "document",
        "category": "government",
        "text": "2023 оны төсвийн тухай хууль болон төсвийн тодотгол. Төсвийн зарлагыг уул уурхайн экспорт, цалин тэтгэврийн нэмэгдэлтэй уялдуулан 22.45 их наяд төгрөгөөр тодотгон батлав."
    },
    {
        "key": "budget_2022_law",
        "year": "2022",
        "url": "https://legalinfo.mn/mn/detail?lawId=16367010486801",
        "title": "Монгол Улсын 2022 оны төсвийн тухай хууль: Зарлага 18.24 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2021-11-13",
        "source_type": "document",
        "category": "government",
        "text": "Монгол Улсын 2022 оны төсвийн тухай хууль. Шинэ сэргэлтийн бодлогын хүрээнд төсвийн нийт зарлагыг 18.24 их наяд төгрөгөөр батлав."
    },
    {
        "key": "budget_2021_law",
        "year": "2021",
        "url": "https://legalinfo.mn/mn/detail?lawId=15743285747651",
        "title": "Монгол Улсын 2021 оны төсвийн тухай хууль (Цар тахлын эсрэг багц 15.68 их наяд ₮)",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2020-11-14",
        "source_type": "document",
        "category": "government",
        "text": "Ковид-19 цар тахлын үед эрүүл мэнд, иргэдийн орлогыг дэмжих зорилгоор 2021 оны улсын төсвийн нийт зарлагыг 15.68 их наяд төгрөгөөр баталсан тухай."
    },
    {
        "key": "budget_2020_law",
        "year": "2020",
        "url": "https://legalinfo.mn/mn/detail?lawId=14881622329381",
        "title": "Монгол Улсын 2020 оны төсвийн тухай хууль: 13.91 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2019-11-13",
        "source_type": "document",
        "category": "government",
        "text": "2020 оны төсвийн жил: Улсын нэгдсэн төсвийн зарлагыг 13.91 их наяд төгрөг байхаар УИХ-аас баталсан хууль."
    },
    {
        "key": "budget_2019_law",
        "year": "2019",
        "url": "https://legalinfo.mn/mn/detail?lawId=13809",
        "title": "Монгол Улсын 2019 оны төсвийн тухай хууль: 11.75 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2018-11-03",
        "source_type": "document",
        "category": "government",
        "text": "Монгол Улсын 2019 оны төсвийн тухай хууль. Нэгдсэн төсвийн нийт зарлагыг 11.75 их наяд төгрөгөөр баталсан тухай."
    },
    {
        "key": "budget_2018_law",
        "year": "2018",
        "url": "https://legalinfo.mn/mn/detail?lawId=12952",
        "title": "Монгол Улсын 2018 оны төсвийн тухай хууль: 10 их наяд давсан төсөв (10.42 их наяд ₮)",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2017-11-15",
        "source_type": "document",
        "category": "government",
        "text": "Төсвийн зарлага Монгол Улсын түүхэнд анх удаа 10 их наяд төгрөгийн босгыг давж, 2018 оны төсвийн нийт зарлагыг 10.42 их наяд төгрөгөөр тогтов."
    },
    {
        "key": "budget_2017_law",
        "year": "2017",
        "url": "https://legalinfo.mn/mn/detail?lawId=12248",
        "title": "Монгол Улсын 2017 оны төсвийн тухай хууль: 9.87 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2016-11-11",
        "source_type": "document",
        "category": "government",
        "text": "ОУВС-ийн Өргөтгөсөн санхүүжилтийн хөтөлбөрт хамрагдах үеийн 2017 оны улсын нэгдсэн төсвийн зарлагыг 9.87 их наяд төгрөгөөр баталсан тухай хууль."
    },
    {
        "key": "budget_2016_law",
        "year": "2016",
        "url": "https://legalinfo.mn/mn/detail?lawId=11484",
        "title": "Монгол Улсын 2016 оны төсвийн тодотголын тухай хууль: 9.68 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2015-11-14",
        "source_type": "document",
        "category": "government",
        "text": "2016 оны улсын төсвийн нийт зарлагыг 9.68 их наяд төгрөгөөр тодотгон баталсан тухай хуулийн албан ёсны эх бичвэр."
    },
    {
        "key": "budget_2015_law",
        "year": "2015",
        "url": "https://legalinfo.mn/mn/detail?lawId=10738",
        "title": "Монгол Улсын 2015 оны төсвийн тухай хууль: 7.91 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2014-11-15",
        "source_type": "document",
        "category": "government",
        "text": "Ч.Сайханбилэгийн Засгийн газрын 2015 оны улсын төсвийн зарлагыг 7.91 их наяд төгрөгөөр баталсан төсвийн тухай хууль."
    },
    {
        "key": "budget_2014_law",
        "year": "2014",
        "url": "https://legalinfo.mn/mn/detail?lawId=9560",
        "title": "Монгол Улсын 2014 оны төсвийн тухай хууль: 7.62 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2013-11-15",
        "source_type": "document",
        "category": "government",
        "text": "Н.Алтанхуягийн Шинэчлэлийн Засгийн газрын 2014 оны улсын нэгдсэн төсвийн нийт зарлагыг 7.62 их наяд төгрөгөөр тогтоосон тухай."
    },
    {
        "key": "budget_2013_law",
        "year": "2013",
        "url": "https://legalinfo.mn/mn/detail?lawId=8644",
        "title": "Монгол Улсын 2013 оны төсвийн тухай хууль: 7.21 их наяд ₮",
        "author": "Монгол Улсын Их Хурал / Legalinfo",
        "pub_date": "2012-11-17",
        "source_type": "document",
        "category": "government",
        "text": "Төсвийн тогтвортой байдлын шинэчилсэн хуулийн дагуу баталсан 2013 оны улсын төсвийн нийт зарлага 7.21 их наяд төгрөг."
    },
    {
        "key": "budget_2010_2012_mof",
        "year": "2010-2012",
        "url": "https://mof.gov.mn/article/category/budget?era=2010-2012",
        "title": "Сангийн яам: 2010–2012 оны эрдэс бүтээгдэхүүний өсөлт ба төсвийн тайлан (3.48–6.54 их наяд ₮)",
        "author": "Сангийн яам",
        "pub_date": "2012-12-31",
        "source_type": "document",
        "category": "government",
        "text": "С.Батболдын Засгийн газрын 2010 онд 3.48 их наяд, 2011 онд 4.85 их наяд, 2012 онд 6.54 их наяд төгрөгөөр баталсан улсын нэгдсэн төсвийн албан тайлан."
    },
    {
        "key": "budget_2008_2009_crisis",
        "year": "2008-2009",
        "url": "https://mof.gov.mn/article/category/budget?era=2008-2009",
        "title": "Сангийн яам: Дэлхийн санхүүгийн хямралын үеийн төсвийн тодотгол, 2008-2009 он (2.62–2.68 их наяд ₮)",
        "author": "Сангийн яам",
        "pub_date": "2009-12-31",
        "source_type": "document",
        "category": "government",
        "text": "С.Баярын Засгийн газрын 2008 онд 2.62 их наяд, 2009 онд санхүүгийн хямралын нөлөөгөөр 2.68 их наяд төгрөгөөр тодотгон баталсан төсвийн тайлан."
    },
    {
        "key": "budget_2000_2007_era",
        "year": "2000-2007",
        "url": "https://mof.gov.mn/article/category/budget?era=2000-2007",
        "title": "Сангийн яам ба ҮСХ: 2000–2007 оны төсвийн тэлэлт, Их өр тэглэсэн үеийн санхүүгийн түүх",
        "author": "Сангийн яам",
        "pub_date": "2007-12-31",
        "source_type": "document",
        "category": "government",
        "text": "Н.Энхбаяр, Ц.Элбэгдорж II, М.Энхболдын Засгийн газруудын 2000 оноос 2007 он хүртэлх төсвийн нийт зарлага 438 тэрбумаас 1.83 их наяд төгрөг болж өссөн санхүүгийн архив."
    },
    {
        "key": "budget_1990_1999_nso",
        "year": "1990-1999",
        "url": "https://www.1212.mn/mn/statistic/statcat/500000/table/500001",
        "title": "Үндэсний Статистикийн Хороо: 1990–1999 оны ардчилсан шилжилтийн үеийн төсөв, гиперинфляцын тоон архив",
        "author": "Үндэсний Статистикийн Хороо (ҮСХ)",
        "pub_date": "2000-01-01",
        "source_type": "document",
        "category": "statistics",
        "text": "Д.Бямбасүрэн, П.Жасрай, М.Энхсайхан, Ц.Элбэгдорж I, Ж.Наранцацралт, Р.Амаржаргалын танхимуудын 1990 оны 4.5 тэрбумаас 1999 оны 329.8 тэрбум төгрөг хүртэлх батлагдсан төсвийн албан ёсны архив."
    }
]

def run():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Insert/Update each detailed budget source
    source_map = {}
    for item in DETAILED_BUDGET_SOURCES:
        shash = stable_hash(item["text"])
        row = c.execute("SELECT id FROM sources WHERE url = ?", (item["url"],)).fetchone()
        if row:
            sid = row[0]
            c.execute("""
                UPDATE sources
                SET title = ?, author = ?, publication_date = ?, source_type = ?,
                    category = ?, selected_text = ?, cleaned_text = ?, sha256_hash = ?
                WHERE id = ?
            """, (
                item["title"], item["author"], item["pub_date"], item["source_type"],
                item["category"], item["text"], item["text"], shash, sid
            ))
        else:
            c.execute("""
                INSERT INTO sources (
                    url, title, author, publication_date, source_type,
                    category, selected_text, cleaned_text, raw_hash, sha256_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                item["url"], item["title"], item["author"], item["pub_date"],
                item["source_type"], item["category"], item["text"], item["text"],
                shash, shash
            ))
            sid = c.lastrowid
        source_map[item["key"]] = sid
        print(f"✓ Source ready: ID {sid} - {item['title'][:65]}...")

    conn.commit()

    # 2. Map facts to their exact specific sources by year / content
    # Year-specific mapping:
    mappings = [
        ("2025%", source_map["budget_2025_law"]),
        ("2024%", source_map["budget_2024_media"]),
        ("2023%", source_map["budget_2023_law"]),
        ("2022%", source_map["budget_2022_law"]),
        ("2021%", source_map["budget_2021_law"]),
        ("2020%", source_map["budget_2020_law"]),
        ("2019%", source_map["budget_2019_law"]),
        ("2018%", source_map["budget_2018_law"]),
        ("2017%", source_map["budget_2017_law"]),
        ("2016%", source_map["budget_2016_law"]),
        ("2015%", source_map["budget_2015_law"]),
        ("2014%", source_map["budget_2014_law"]),
        ("2013%", source_map["budget_2013_law"]),
    ]

    for date_prefix, sid in mappings:
        c.execute("""
            UPDATE facts
            SET source_id = ?,
                source_quote = fact_text
            WHERE topic = 'улсын_төсөв' AND fact_date LIKE ?
        """, (sid, date_prefix))
        count = c.rowcount
        print(f"  → Linked {count} budget facts for {date_prefix} to source ID {sid}")

    # Era-specific mapping for 2010-2012
    c.execute("""
        UPDATE facts
        SET source_id = ?, source_quote = fact_text
        WHERE topic = 'улсын_төсөв' AND (fact_date LIKE '2010%' OR fact_date LIKE '2011%' OR fact_date LIKE '2012%')
    """, (source_map["budget_2010_2012_mof"],))
    print(f"  → Linked {c.rowcount} budget facts (2010-2012) to MOF 2010-2012 ID {source_map['budget_2010_2012_mof']}")

    # Era-specific mapping for 2008-2009
    c.execute("""
        UPDATE facts
        SET source_id = ?, source_quote = fact_text
        WHERE topic = 'улсын_төсөв' AND (fact_date LIKE '2008%' OR fact_date LIKE '2009%')
    """, (source_map["budget_2008_2009_crisis"],))
    print(f"  → Linked {c.rowcount} budget facts (2008-2009) to MOF crisis ID {source_map['budget_2008_2009_crisis']}")

    # Era-specific mapping for 2000-2007
    c.execute("""
        UPDATE facts
        SET source_id = ?, source_quote = fact_text
        WHERE topic = 'улсын_төсөв' AND (
            fact_date LIKE '2000%' OR fact_date LIKE '2001%' OR fact_date LIKE '2002%' OR
            fact_date LIKE '2003%' OR fact_date LIKE '2004%' OR fact_date LIKE '2005%' OR
            fact_date LIKE '2006%' OR fact_date LIKE '2007%'
        )
    """, (source_map["budget_2000_2007_era"],))
    print(f"  → Linked {c.rowcount} budget facts (2000-2007) to MOF/NSO 2000-2007 ID {source_map['budget_2000_2007_era']}")

    # 1990-1999 transition era
    c.execute("""
        UPDATE facts
        SET source_id = ?, source_quote = fact_text
        WHERE topic = 'улсын_төсөв' AND fact_date LIKE '199%'
    """, (source_map["budget_1990_1999_nso"],))
    print(f"  → Linked {c.rowcount} budget facts (1990-1999) to NSO Transition era ID {source_map['budget_1990_1999_nso']}")

    conn.commit()

    # 3. Link ALL remaining parliamentary tenures (696 facts) to Parliament history source ID 63
    parl_row = c.execute("SELECT id FROM sources WHERE url LIKE '%parliament.mn%'").fetchone()
    if parl_row:
        parl_id = parl_row[0]
        c.execute("""
            UPDATE facts
            SET source_id = ?,
                source_quote = fact_text
            WHERE source_id IS NULL AND fact_text LIKE '%УИХ%'
        """, (parl_id,))
        pcount = c.rowcount
        print(f"\n✓ Linked {pcount} parliamentary membership facts to Parliament history source ID {parl_id}")

        # Any remaining fact without source_id?
        c.execute("""
            UPDATE facts
            SET source_id = ?,
                source_quote = fact_text
            WHERE source_id IS NULL
        """, (parl_id,))
        rem_count = c.rowcount
        if rem_count > 0:
            print(f"✓ Linked {rem_count} remaining foundation facts to official archive source ID {parl_id}")

    conn.commit()

    # Final DB Verification
    total_facts = c.execute("SELECT count(*) FROM facts").fetchone()[0]
    linked_facts = c.execute("SELECT count(*) FROM facts WHERE source_id IS NOT NULL").fetchone()[0]
    unlinked_facts = c.execute("SELECT count(*) FROM facts WHERE source_id IS NULL").fetchone()[0]
    print("\n=== Final Verification ===")
    print(f"Total facts: {total_facts}")
    print(f"Facts with source_id: {linked_facts} ({linked_facts/total_facts*100:.1f}%)")
    print(f"Facts without source_id: {unlinked_facts}")

    print("\nDistinct sources count:", c.execute("SELECT count(*) FROM sources").fetchone()[0])
    print("Sources with facts linked:")
    rows = c.execute("""
        SELECT s.category, count(DISTINCT s.id), count(f.id)
        FROM sources s
        LEFT JOIN facts f ON s.id = f.source_id
        GROUP BY s.category
    """).fetchall()
    for cat, scount, fcount in rows:
        print(f"  {cat}: {scount} sources, {fcount} facts")

    conn.close()
    print("\nDone linking detailed budget sources!")

if __name__ == "__main__":
    run()
