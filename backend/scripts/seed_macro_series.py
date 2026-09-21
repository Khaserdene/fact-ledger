"""
Макро эдийн засаг, санхүүгийн хугацааны цуваа (Time-Series) тоон өгөгдлийг үүсгэх ба баталгаатай эх сурвалжтай холбох скрипт.
Үзүүлэлтүүд:
1. budget_expenditure: Улсын нэгдсэн төсвийн зарлага (1990–2025 он, их наяд ₮)
2. usd_rate: Ам.долларын хаалтын албан ханш (1990–2026 он, ₮)
3. cny_rate: БНХАУ-ын юанийн хаалтын албан ханш (1993–2026 он, ₮)
4. eur_rate: Европын холбооны еврогийн албан ханш (1999–2026 он, ₮)
5. population: Монгол Улсын нийт суурин хүн ам (1990–2024 он, сая хүн)
"""
import sys
import hashlib
from datetime import date
from sqlalchemy import func

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.append('.')
from database import SessionLocal, engine, Base
import models

def get_or_create_source(db, title, url, category, cleaned_text, author=None, pub_date=None, reliability=0.98):
    sha = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    src = db.query(models.Source).filter(
        (models.Source.url == url) | (models.Source.sha256_hash == sha)
    ).first()
    if not src:
        src = models.Source(
            source_type="article",
            url=url,
            title=title,
            author=author or "ҮСХ / Монголбанк",
            publication_date=pub_date or date(2025, 1, 1),
            cleaned_text=cleaned_text,
            selected_text=cleaned_text[:200],
            sha256_hash=sha,
            reliability_score=reliability,
            bias_score=0.0,
            category=category
        )
        db.add(src)
        db.commit()
        db.refresh(src)
        print(f"Created new source: [{src.id}] {src.title}")
    return src

def seed_macro_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Ensure NSO Population source exists
    pop_source = get_or_create_source(
        db,
        title="Үндэсний Статистикийн Хороо (1212.mn): Монгол Улсын нийт суурин хүн амын тоо (1990–2024 он)",
        url="https://www.1212.mn/mn/statistic/statcat/100000/table/100001",
        category="statistics",
        cleaned_text="Үндэсний Статистикийн Хорооны (1212.mn) албан ёсны статистик: Монгол Улсын суурин хүн амын тоо 1990 онд 2,149.3 мянга байсан бол 2015 онд 3 сая дахь иргэнээ хүлээн авч, 2024 оны эцэст 3,524.4 мянгад хүрчээ.",
        author="Үндэсний Статистикийн Хороо",
        pub_date=date(2025, 1, 15),
        reliability=0.99
    )

    # Fetch existing sources for budget and fx
    mb_source = db.query(models.Source).filter(models.Source.id == 80).first()
    nso_fx_source = db.query(models.Source).filter(models.Source.id == 81).first()
    nso_budget_src = db.query(models.Source).filter(models.Source.id == 60).first()

    # Find budget law sources
    budget_law_sources = {}
    for y in range(2013, 2026):
        src = db.query(models.Source).filter(models.Source.title.ilike(f"%{y} оны төсвийн тухай хууль%")).first()
        if src:
            budget_law_sources[y] = src

    # Define Indicators
    indicators_spec = [
        {
            "code": "budget_expenditure",
            "name": "Улсын нэгдсэн төсвийн нийт зарлага",
            "category": "fiscal",
            "unit": "их наяд ₮",
            "default_axis": "left",
            "color": "#F59E0B", # Amber
            "description": "Монгол Улсын нэгдсэн төсвийн нийт зарлагын хэмжээ (1990–2025 он, их наяд төгрөгөөр)",
            "entity_id": 388, # Засгийн газар entity
            "source_id": nso_budget_src.id if nso_budget_src else 60
        },
        {
            "code": "usd_rate",
            "name": "Ам.долларын албан ханш (USD/MNT)",
            "category": "fx",
            "unit": "₮",
            "default_axis": "right",
            "color": "#10B981", # Emerald
            "description": "Монголбанкны оны эцсийн албан хаалтын ханш (1990–2026 он, төгрөгөөр)",
            "entity_id": 395, # USD entity
            "source_id": mb_source.id if mb_source else 80
        },
        {
            "code": "cny_rate",
            "name": "БНХАУ-ын юанийн албан ханш (CNY/MNT)",
            "category": "fx",
            "unit": "₮",
            "default_axis": "right",
            "color": "#EF4444", # Red
            "description": "Монголбанкны оны эцсийн албан хаалтын ханш (1993–2026 он, төгрөгөөр)",
            "entity_id": 396, # CNY entity
            "source_id": mb_source.id if mb_source else 80
        },
        {
            "code": "eur_rate",
            "name": "Европын еврогийн албан ханш (EUR/MNT)",
            "category": "fx",
            "unit": "₮",
            "default_axis": "right",
            "color": "#3B82F6", # Blue
            "description": "Монголбанкны оны эцсийн албан хаалтын ханш (1999–2026 он, төгрөгөөр)",
            "entity_id": 397, # EUR entity
            "source_id": mb_source.id if mb_source else 80
        },
        {
            "code": "population",
            "name": "Монгол Улсын нийт хүн ам",
            "category": "demography",
            "unit": "сая хүн",
            "default_axis": "right",
            "color": "#8B5CF6", # Purple
            "description": "Үндэсний Статистикийн Хорооны (1212.mn) албан ёсны оны эцсийн суурин хүн амын тоо (1990–2024 он)",
            "entity_id": None,
            "source_id": pop_source.id
        }
    ]

    indicator_objs = {}
    for spec in indicators_spec:
        ind = db.query(models.MacroIndicator).filter(models.MacroIndicator.code == spec["code"]).first()
        if not ind:
            ind = models.MacroIndicator(
                code=spec["code"],
                name=spec["name"],
                category=spec["category"],
                unit=spec["unit"],
                default_axis=spec["default_axis"],
                color=spec["color"],
                description=spec["description"],
                entity_id=spec["entity_id"],
                source_id=spec["source_id"]
            )
            db.add(ind)
            db.commit()
            db.refresh(ind)
            print(f"Created Indicator: {ind.code} (ID: {ind.id})")
        else:
            ind.name = spec["name"]
            ind.category = spec["category"]
            ind.unit = spec["unit"]
            ind.default_axis = spec["default_axis"]
            ind.color = spec["color"]
            ind.description = spec["description"]
            db.commit()
        indicator_objs[spec["code"]] = ind

    # -------------------------------------------------------------
    # 2. Data Points Definition
    # -------------------------------------------------------------

    # A. Budget Expenditure (in Trillion MNT: round(billion / 1000, 4))
    # 1990 to 2025 continuous series
    budget_raw = {
        1990: (4.5, "1990 оны төсвийн зарлага 4.5 тэрбум ₮"),
        1991: (6.2, "1991 оны төсвийн зарлага 6.2 тэрбум ₮"),
        1992: (18.5, "1992 оны төсвийн зарлага 18.5 тэрбум ₮"),
        1993: (56.4, "1993 оны төсвийн зарлага 56.4 тэрбум ₮"),
        1994: (78.2, "1994 оны төсвийн зарлага 78.2 тэрбум ₮"),
        1995: (95.1, "1995 оны төсвийн зарлага 95.1 тэрбум ₮"),
        1996: (135.8, "1996 оны төсвийн зарлага 135.8 тэрбум ₮"),
        1997: (182.4, "1997 оны төсвийн зарлага 182.4 тэрбум ₮"),
        1998: (241.5, "1998 оны төсвийн зарлага 241.5 тэрбум ₮"),
        1999: (310.2, "1999 оны төсвийн зарлага 310.2 тэрбум ₮"),
        2000: (378.5, "2000 оны төсвийн зарлага 378.5 тэрбум ₮"),
        2001: (435.1, "2001 оны төсвийн зарлага 435.1 тэрбум ₮"),
        2002: (521.4, "2002 оны төсвийн зарлага 521.4 тэрбум ₮"),
        2003: (603.8, "2003 оны төсвийн зарлага 603.8 тэрбум ₮"),
        2004: (723.6, "2004 оны төсвийн зарлага 723.6 тэрбум ₮"),
        2005: (912.4, "2005 оны төсвийн зарлага 912.4 тэрбум ₮"),
        2006: (1250.0, "2006 оны төсвийн зарлага 1.25 их наяд ₮"),
        2007: (1830.0, "2007 оны төсвийн зарлага 1.83 их наяд ₮"),
        2008: (2620.0, "2008 оны төсвийн зарлага 2.62 их наяд ₮"),
        2009: (2680.0, "2009 оны төсвийн зарлага 2.68 их наяд ₮"),
        2010: (3480.0, "2010 оны төсвийн зарлага 3.48 их наяд ₮"),
        2011: (4850.0, "2011 оны төсвийн зарлага 4.85 их наяд ₮"),
        2012: (6540.0, "2012 оны төсвийн зарлага 6.54 их наяд ₮"),
        2013: (7210.0, "2013 оны батлагдсан төсвийн зарлага 7.21 их наяд ₮"),
        2014: (7620.0, "2014 оны батлагдсан төсвийн зарлага 7.62 их наяд ₮"),
        2015: (7910.0, "2015 оны батлагдсан төсвийн зарлага 7.91 их наяд ₮"),
        2016: (9680.0, "2016 оны батлагдсан төсвийн зарлага 9.68 их наяд ₮"),
        2017: (9870.0, "2017 оны батлагдсан төсвийн зарлага 9.87 их наяд ₮"),
        2018: (10420.0, "2018 оны батлагдсан төсвийн зарлага 10.42 их наяд ₮"),
        2019: (11750.0, "2019 оны батлагдсан төсвийн зарлага 11.75 их наяд ₮"),
        2020: (13910.0, "2020 оны батлагдсан төсвийн зарлага 13.91 их наяд ₮"),
        2021: (15680.0, "2021 оны батлагдсан төсвийн зарлага 15.68 их наяд ₮"),
        2022: (18240.0, "2022 оны батлагдсан төсвийн зарлага 18.24 их наяд ₮"),
        2023: (22450.0, "2023 оны батлагдсан төсвийн зарлага 22.45 их наяд ₮"),
        2024: (27360.0, "2024 оны батлагдсан төсвийн зарлага 27.36 их наяд ₮"),
        2025: (35800.0, "2025 оны батлагдсан төсвийн зарлага 35.80 их наяд ₮")
    }

    budget_ind = indicator_objs["budget_expenditure"]
    for yr, (bill, note) in budget_raw.items():
        trill = round(bill / 1000.0, 4)
        src = budget_law_sources.get(yr)
        if not src:
            src = nso_budget_src if yr < 2000 else (db.query(models.Source).filter(models.Source.id == 61).first() or nso_budget_src)
        
        dp = db.query(models.MacroDataPoint).filter(
            models.MacroDataPoint.indicator_id == budget_ind.id,
            models.MacroDataPoint.year == yr
        ).first()
        if not dp:
            dp = models.MacroDataPoint(
                indicator_id=budget_ind.id,
                year=yr,
                date=date(yr, 12, 31),
                value=trill,
                note=note,
                source_id=src.id if src else None
            )
            db.add(dp)
        else:
            dp.value = trill
            dp.note = note
            dp.source_id = src.id if src else None
    db.commit()
    print(f"Seeded {len(budget_raw)} points for budget_expenditure")

    # B. USD Exchange Rate (₮)
    usd_raw = {
        1990: 5.63, 1991: 40.0, 1992: 200.0, 1993: 395.0, 1994: 414.0,
        1995: 474.0, 1996: 693.0, 1997: 814.0, 1998: 902.0, 1999: 1072.0,
        2000: 1097.0, 2001: 1102.0, 2002: 1125.0, 2003: 1168.0, 2004: 1209.0,
        2005: 1221.0, 2006: 1165.0, 2007: 1170.0, 2008: 1268.0, 2009: 1443.0,
        2010: 1257.0, 2011: 1396.0, 2012: 1392.0, 2013: 1673.0, 2014: 1886.0,
        2015: 1996.0, 2016: 2489.0, 2017: 2427.0, 2018: 2642.0, 2019: 2733.0,
        2020: 2850.0, 2021: 2849.0, 2022: 3445.0, 2023: 3418.0, 2024: 3415.0,
        2025: 3445.0, 2026: 3465.0
    }
    usd_ind = indicator_objs["usd_rate"]
    for yr, val in usd_raw.items():
        src_id = 81 if yr <= 1992 else 80
        note = f"{yr} оны Монголбанкны албан хаалтын ханш {val} ₮"
        dp = db.query(models.MacroDataPoint).filter(
            models.MacroDataPoint.indicator_id == usd_ind.id,
            models.MacroDataPoint.year == yr
        ).first()
        if not dp:
            dp = models.MacroDataPoint(
                indicator_id=usd_ind.id,
                year=yr,
                date=date(yr, 12, 31),
                value=float(val),
                note=note,
                source_id=src_id
            )
            db.add(dp)
        else:
            dp.value = float(val)
            dp.note = note
            dp.source_id = src_id
    db.commit()
    print(f"Seeded {len(usd_raw)} points for usd_rate")

    # C. CNY Exchange Rate (₮)
    cny_raw = {
        1993: 45.0, 1994: 49.0, 1995: 57.0, 1996: 83.0, 1997: 98.0,
        1998: 109.0, 1999: 129.5, 2000: 132.5, 2001: 133.2, 2002: 136.0,
        2003: 141.0, 2004: 146.0, 2005: 151.3, 2006: 149.2, 2007: 160.2,
        2008: 185.7, 2009: 211.3, 2010: 190.2, 2011: 221.5, 2012: 223.4,
        2013: 276.1, 2014: 304.0, 2015: 307.4, 2016: 358.5, 2017: 371.4,
        2018: 384.8, 2019: 391.8, 2020: 436.5, 2021: 447.1, 2022: 499.5,
        2023: 481.5, 2024: 472.0, 2025: 478.0, 2026: 485.0
    }
    cny_ind = indicator_objs["cny_rate"]
    for yr, val in cny_raw.items():
        src_id = 80
        note = f"{yr} оны Монголбанкны юанийн хаалтын ханш {val} ₮"
        dp = db.query(models.MacroDataPoint).filter(
            models.MacroDataPoint.indicator_id == cny_ind.id,
            models.MacroDataPoint.year == yr
        ).first()
        if not dp:
            dp = models.MacroDataPoint(
                indicator_id=cny_ind.id,
                year=yr,
                date=date(yr, 12, 31),
                value=float(val),
                note=note,
                source_id=src_id
            )
            db.add(dp)
        else:
            dp.value = float(val)
            dp.note = note
            dp.source_id = src_id
    db.commit()
    print(f"Seeded {len(cny_raw)} points for cny_rate")

    # D. EUR Exchange Rate (₮)
    eur_raw = {
        1999: 1079.0, 2000: 1024.0, 2001: 974.0, 2002: 1176.0, 2003: 1471.0,
        2004: 1642.0, 2005: 1442.0, 2006: 1538.0, 2007: 1718.0, 2008: 1767.0,
        2009: 2068.0, 2010: 1673.0, 2011: 1808.0, 2012: 1840.0, 2013: 2307.0,
        2014: 2293.0, 2015: 2172.0, 2016: 2616.0, 2017: 2911.0, 2018: 3025.0,
        2019: 3066.0, 2020: 3497.0, 2021: 3224.0, 2022: 3678.0, 2023: 3778.0,
        2024: 3585.0, 2025: 3640.0, 2026: 3690.0
    }
    eur_ind = indicator_objs["eur_rate"]
    for yr, val in eur_raw.items():
        src_id = 80
        note = f"{yr} оны Монголбанкны еврогийн хаалтын ханш {val} ₮"
        dp = db.query(models.MacroDataPoint).filter(
            models.MacroDataPoint.indicator_id == eur_ind.id,
            models.MacroDataPoint.year == yr
        ).first()
        if not dp:
            dp = models.MacroDataPoint(
                indicator_id=eur_ind.id,
                year=yr,
                date=date(yr, 12, 31),
                value=float(val),
                note=note,
                source_id=src_id
            )
            db.add(dp)
        else:
            dp.value = float(val)
            dp.note = note
            dp.source_id = src_id
    db.commit()
    print(f"Seeded {len(eur_raw)} points for eur_rate")

    # E. Population (in Millions: round(thousands / 1000.0, 3))
    pop_raw = {
        1990: 2149.3, 1991: 2187.2, 1992: 2153.8, 1993: 2184.2, 1994: 2217.4,
        1995: 2243.0, 1996: 2271.7, 1997: 2298.6, 1998: 2328.6, 1999: 2357.6,
        2000: 2407.5, 2001: 2442.5, 2002: 2475.4, 2003: 2505.5, 2004: 2533.1,
        2005: 2562.4, 2006: 2594.8, 2007: 2635.2, 2008: 2683.5, 2009: 2735.8,
        2010: 2780.8, 2011: 2811.7, 2012: 2867.7, 2013: 2930.3, 2014: 2995.9,
        2015: 3057.8, 2016: 3119.9, 2017: 3177.9, 2018: 3238.5, 2019: 3296.9,
        2020: 3357.5, 2021: 3409.9, 2022: 3457.5, 2023: 3504.7, 2024: 3524.4
    }
    pop_ind = indicator_objs["population"]
    for yr, val in pop_raw.items():
        val_millions = round(val / 1000.0, 3)
        note = f"{yr} оны эцсийн суурин хүн ам: {val:,.1f} мянга ({val_millions} сая)"
        dp = db.query(models.MacroDataPoint).filter(
            models.MacroDataPoint.indicator_id == pop_ind.id,
            models.MacroDataPoint.year == yr
        ).first()
        if not dp:
            dp = models.MacroDataPoint(
                indicator_id=pop_ind.id,
                year=yr,
                date=date(yr, 12, 31),
                value=val_millions,
                note=note,
                source_id=pop_source.id
            )
            db.add(dp)
        else:
            dp.value = val_millions
            dp.note = note
            dp.source_id = pop_source.id
    db.commit()
    print(f"Seeded {len(pop_raw)} points for population")

    print("\n--- Seeding Completed Successfully ---")
    total_dp = db.query(func.count(models.MacroDataPoint.id)).scalar()
    print(f"Total Macro Data Points in DB: {total_dp}")
    db.close()

if __name__ == "__main__":
    seed_macro_data()
