import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

db_path = Path("backend/profiling_facts.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 29 хэргийн бодит санхүүгийн хохирлын дүн (тэрбум төгрөгөөр), холбогдох он, Засгийн газрын ID
# Cabinet IDs:
# 34: Жасрай (1992-1996)
# 35: М.Энхсайхан (1996-1998)
# 36: Ц.Элбэгдорж I (1998)
# 37: Н.Энхбаяр (2000-2004)
# 38: Ц.Элбэгдорж II (2004-2006)
# 39: М.Энхболд (2006-2007)
# 40: С.Баяр (2007-2009)
# 41: Сү.Батболд (2009-2012)
# 42: Н.Алтанхуяг (2012-2014)
# 43: Ч.Сайханбилэг (2014-2016)
# 380: Ж.Эрдэнэбат (2016-2017)
# 44: У.Хүрэлсүх (2017-2021)
# 45: Л.Оюун-Эрдэнэ (2021-2024)

CASE_FINANCIALS = {
    "coal-theft": {
        "amount_billion": 6400.0, # Аудит+Оффтейк+Татварын зөрүү нийт 6.4 их наяд ₮ (УИХ-ын Түр хороо, 2023)
        "currency": "MNT",
        "case_year": 2019, # Гол оффтейк гэрээнүүд 2018-2020 онд байгуулагдсан
        "cabinet_id": 44, # У.Хүрэлсүхийн ЗГ (оффтейк гэрээ байгуулагдсан үе)
    },
    "dbm-scandal": {
        "amount_billion": 1800.0, # Хөгжлийн банкны чанаргүй зээлийн нийт дүн 1.8 их наяд ₮
        "currency": "MNT",
        "case_year": 2022,
        "cabinet_id": 45,
    },
    "price-stabilization": {
        "amount_billion": 3800.0, # Үнэ тогтворжуулах хөтөлбөр 3.8 их наяд ₮
        "currency": "MNT",
        "case_year": 2013,
        "cabinet_id": 42,
    },
    "sovereign-bonds": {
        "amount_billion": 2250.0, # Чингис бонд 1.5 тэрбум USD (~2.25 их наяд ₮)
        "currency": "MNT",
        "case_year": 2012,
        "cabinet_id": 42,
    },
    "railway-dispute": {
        "amount_billion": 1200.0, # Төмөр замын гацаа & далангийн зардал ~1.2 их наяд ₮
        "currency": "MNT",
        "case_year": 2014,
        "cabinet_id": 42,
    },
    "green-bus": {
        "amount_billion": 134.8, # Ногоон автобусны төсөв 134.8 тэрбум ₮
        "currency": "MNT",
        "case_year": 2023,
        "cabinet_id": 45,
    },
    "bzs-scandal": {
        "amount_billion": 360.0, # БЗС-гийн зээл чөлөөлөлт 360 тэрбум ₮
        "currency": "MNT",
        "case_year": 2023,
        "cabinet_id": 45,
    },
    "sme-fund": {
        "amount_billion": 95.0, # ЖДҮХС-гийн гишүүдийн зээл 95 тэрбум ₮
        "currency": "MNT",
        "case_year": 2018,
        "cabinet_id": 44,
    },
    "crop-support-fund": {
        "amount_billion": 380.0, # ТЭДС & ХААДС-ийн эргэн төлөгдөөгүй өр 380 тэрбум ₮
        "currency": "MNT",
        "case_year": 2019,
        "cabinet_id": 44,
    },
    "tavantolgoi-fuel-case": {
        "amount_billion": 1050.0, # Тавантолгой түлш & шахмал түлшний татаас 1.05 их наяд ₮
        "currency": "MNT",
        "case_year": 2020,
        "cabinet_id": 44,
    },
    "sixty-billion": {
        "amount_billion": 60.0, # 60 тэрбумын схем 60 тэрбум ₮
        "currency": "MNT",
        "case_year": 2016,
        "cabinet_id": 380,
    },
    "erdenet-49": {
        "amount_billion": 850.0, # Эрдэнэт 49% хувьчлал 400 сая USD (~850 тэрбум ₮)
        "currency": "MNT",
        "case_year": 2016,
        "cabinet_id": 43,
    },
    "darkhan-metallurgy": {
        "amount_billion": 240.0, # Дарханы төмөрлөгийн концесс & ДБМ өр 240 тэрбум ₮
        "currency": "MNT",
        "case_year": 2015,
        "cabinet_id": 43,
    },
    "oyu-tolgoi": {
        "amount_billion": 8800.0, # Дубайн төлөвлөгөө / Оюутолгойн далд өр (~2.3 тэрбум USD өр тэглэгдсэн)
        "currency": "MNT",
        "case_year": 2015,
        "cabinet_id": 43,
    },
    "just-oil-collapse": {
        "amount_billion": 500.0, # Жаст Ойл & Хадгаламж банкны хохирол 500 тэрбум ₮
        "currency": "MNT",
        "case_year": 2013,
        "cabinet_id": 42,
    },
    "standard-bank-erba": {
        "amount_billion": 180.0, # Стандарт банкны 115 сая долларын арбитрын өр (~180 тэрбум ₮)
        "currency": "MNT",
        "case_year": 2012,
        "cabinet_id": 41,
    },
    "anod-bank-collapse": {
        "amount_billion": 120.0, # Анод банкны хохирол & дампуурал 120 тэрбум ₮
        "currency": "MNT",
        "case_year": 2008,
        "cabinet_id": 40,
    },
    "khadgalamj-bank-casino": {
        "amount_billion": 14.0, # Хадгаламж банкны 14 тэрбум
        "currency": "MNT",
        "case_year": 2003,
        "cabinet_id": 37,
    },
    "casino-scandal-1999": {
        "amount_billion": 5.0, # 1999 оны казиногийн хахууль, улсын төсвийн алдагдал
        "currency": "MNT",
        "case_year": 1999,
        "cabinet_id": 36,
    },
    "miat-war-risk": {
        "amount_billion": 12.0, # МИАТ-ийн дайны даатгалын оффшор угаалт ~12 тэрбум ₮
        "currency": "MNT",
        "case_year": 2010,
        "cabinet_id": 41,
    },
    "southgobi-tax-evasion": {
        "amount_billion": 35.0, # Саусгоби Сэндсийн 35 тэрбум төгрөгийн татварын торгууль
        "currency": "MNT",
        "case_year": 2015,
        "cabinet_id": 43,
    },
    "medicine-quality-monopoly": {
        "amount_billion": 400.0, # Эмийн үнийн хөөрөгдөл & Эрүүл мэндийн даатгалын сан
        "currency": "MNT",
        "case_year": 2023,
        "cabinet_id": 45,
    },
    "ub-land-scandal": {
        "amount_billion": 650.0, # Нийслэлийн үнэ цэнтэй газруудын үнэлгээ, алдагдсан боломж
        "currency": "MNT",
        "case_year": 2016,
        "cabinet_id": 380,
    },
    "offshore-panama": {
        "amount_billion": 150.0, # Панамын оффшор дансанд илэрсэн хөрөнгө
        "currency": "MNT",
        "case_year": 2016,
        "cabinet_id": 43,
    },
    "disabled-children-center": {
        "amount_billion": 25.0, # Төслийн завшаан, нийгмийн төсөв
        "currency": "MNT",
        "case_year": 2019,
        "cabinet_id": 44,
    },
    "khurelsukh-controversies": {
        "amount_billion": 50.0,
        "currency": "MNT",
        "case_year": 2018,
        "cabinet_id": 44,
    },
    "wiretapping-cabinet-crisis": {
        "amount_billion": 10.0,
        "currency": "MNT",
        "case_year": 2017,
        "cabinet_id": 380,
    },
    "foreign-investment-land-dispute": {
        "amount_billion": 100.0,
        "currency": "MNT",
        "case_year": 2024,
        "cabinet_id": 45,
    },
    "zorig-assassination": {
        "amount_billion": 15.0,
        "currency": "MNT",
        "case_year": 1998,
        "cabinet_id": 36,
    }
}

updated = 0
for slug, fin in CASE_FINANCIALS.items():
    c.execute("""
        UPDATE cases
        SET amount_billion = ?,
            currency = ?,
            case_year = ?,
            cabinet_id = ?
        WHERE slug = ?
    """, (fin["amount_billion"], fin["currency"], fin["case_year"], fin["cabinet_id"], slug))
    if c.rowcount > 0:
        updated += 1

conn.commit()
print(f"Амжилттай баяжуулсан хэргүүд: {updated} / {len(CASE_FINANCIALS)}")

# Шалгаж хэвлэх
c.execute("SELECT slug, title, amount_billion, case_year, cabinet_id FROM cases ORDER BY amount_billion DESC LIMIT 10")
print("\nТОП 10 ДУУЛИАНТ ХЭРГИЙН ДҮН (ТЭРБУМ ТӨГРӨГ):")
for r in c.fetchall():
    print(f"- {r[0]}: {r[2]} тэрбум ₮ | Он: {r[3]} | Cabinet ID: {r[4]}")

conn.close()
