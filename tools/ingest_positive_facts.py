# -*- coding: utf-8 -*-
"""Эерэг баримтууд — Говийг ойжуулагч Д.Бараадууз болон E-Mongolia цахим шилжилт."""

import os
import sys

# Backend модулиудыг ашиглах
sys.path.insert(0, os.path.abspath("backend"))
sys.stdout.reconfigure(encoding="utf-8")

from database import SessionLocal
import models
from services.dates import parse_flexible_date
from services import importing
from hasher import stable_hash
import scraper


def verify_substring(quote, text, label):
    if quote not in text:
        raise ValueError(f"CRITICAL: Quote not in selected_text for '{label}'!\nQuote: {quote[:80]}...")


def ingest():
    db = SessionLocal()
    try:
        # =========================================================================
        # 1. ДЭМЧИГИЙН БАРААДУУЗ (Хөдөлмөрийн баатар, Говийн ойжуулагч)
        # =========================================================================
        print(">>> Ingesting Entity 1: Дэмчигийн Бараадууз...")
        baraaduuz = db.query(models.Entity).filter(models.Entity.name == "Дэмчигийн Бараадууз").first()
        if not baraaduuz:
            baraaduuz = models.Entity(
                name="Дэмчигийн Бараадууз",
                entity_type="person",
                description="Монгол Улсын Хөдөлмөрийн баатар, Байгаль орчны гавьяат ажилтан, Өмнөговь аймгийн ойжуулагч. Элсэн говьд 30 гаруй жил тууштай мод тарьж, 400 мянга гаруй тарьц суулгац бойжуулан говь цөлжилтийн эсрэг бодит үр дүнд хүрсэн эрхэм.",
                tldr_summary="Говьд 30 гаруй жил тууштай мод тарьж, 500 га ойжуулалтын эхлэлийг тавьсан Хөдөлмөрийн баатар.",
                is_stub=False,
            )
            db.add(baraaduuz)
            db.flush()

            # Aliases
            for al, kd in [
                ("Д.Бараадууз", "initials"),
                ("Бараадууз", "other"),
                ("Дэмчиг овогтой Бараадууз", "patronymic"),
            ]:
                alias_norm = al.lower().strip()
                db.add(models.EntityAlias(entity_id=baraaduuz.id, alias=al, alias_norm=alias_norm, kind=kd))
            db.flush()
            print(f"Created Entity: {baraaduuz.name} (id={baraaduuz.id})")
        else:
            print(f"Found Existing Entity: {baraaduuz.name} (id={baraaduuz.id})")

        # Source 1: Ergelt.mn interview
        s1_url = "https://ergelt.mn/news_full/111/single/11732"
        s1_title = "Хөдөлмөрийн баатар Д.БАРААДУУЗ: Мод хүний “хэл” мэддэг ч байж мэднэ"
        source1 = db.query(models.Source).filter(models.Source.url == s1_url).first()
        
        # We fetch blocks directly from scraper or construct selected_blocks
        scraped1 = scraper.scrape(s1_url)
        blocks1 = [
            b["text"].strip() for b in scraped1.get("blocks", [])
            if b["type"] in ("p", "h2", "h3", "li", "blockquote") and len(b["text"].strip()) > 10
            and not b["text"].startswith("Монгол Улс, Улаанбаатар хот")
            and not b["text"].startswith("[email")
        ]
        s1_selected_text = "\n\n".join(blocks1)

        if not source1:
            source1 = models.Source(
                source_type="article",
                category="media",
                url=s1_url,
                title=s1_title,
                author="Б.Бадамзул, Эргэлт.мн",
                publication_date=parse_flexible_date("2021-07-20")[0],
                cleaned_text=s1_selected_text,
                selected_text=s1_selected_text,
                raw_hash=stable_hash(s1_selected_text),
                sha256_hash=stable_hash(s1_selected_text),
                bias_score=0.9,
                reliability_score=0.95,
            )
            db.add(source1)
            db.flush()
            print(f"Created Source 1: {source1.title} (id={source1.id})")
        else:
            print(f"Found Existing Source 1: (id={source1.id})")

        # Define rich facts for Baraaduuz
        b_facts_bio = [
            {
                "fact": "Монгол Улсын Хөдөлмөрийн баатар, Байгаль орчны гавьяат цолтой.",
                "source_quote": "Монгол Улсын Хөдөлмөрийн баатар, Байгаль орчны гавьяат Д.Бараадууз",
                "role_context": "Цол хэргэм",
                "tags": ["цол_шагнал", "баатар", "эерэг_нөлөө"],
            },
            {
                "fact": "Анх тэтгэврийнхээ мөнгөөр бензин тос, мотор, ус татах механизм, худаг гаргуулах ажлыг санхүүжүүлэн говьд мод тарих ажлыг эхлүүлсэн.",
                "source_quote": "бензин тос, мотор, ус татдаг механизм, худаг гаргуулах гэх мэт ажилд л тэтгэврийнхээ хэдийг зарцуулсан хэрэг",
                "role_context": "Санхүүжилт ба эхлэл",
                "tags": ["эхлэл", "хувийн_санаачилга", "тууштай_байдал"],
            },
            {
                "fact": "Мод үржүүлгийн газраасаа нийт 400 мянга гаруй тарьц, суулгацыг 9 аймаг, нийслэлийн 6 дүүрэгт нийлүүлж борлуулсан.",
                "source_quote": "400 мянга гаруй тарьц, суулгац гадагш нь борлуулсан",
                "role_context": "Бүтээн байгуулалт ба үр дүн",
                "tags": ["үр_дүн", "мод_үржүүлэг", "ойжуулалт"],
            },
            {
                "fact": "Эхэндээ 1 га талбайд мод тарьж эхэлж байсан бол сүүлд 16 га газарт говийн ховордож буй ургамлыг тарималжуулдаг болсон.",
                "source_quote": "Эхэндээ нэг га талбайд мод тарьж байсан юм. Одоо 16 га газарт говийн ховордож байгаа ургамлыг голцуу тарималжуулдаг",
                "role_context": "Талбайн өргөжилт",
                "tags": ["хүрээ", "тарималжуулалт", "байгаль_хамгаалал"],
            },
            {
                "fact": "Элсэн говьд жимс тарьж туршин алим, үхрийн нүд, чацаргана, бөөрөлзгөнө зэрэг 6-7 төрлийн жимс хураан авдаг болсон.",
                "source_quote": "говьд жимс тарьж болох нь уу гэдгийг туршиж, одоо зургаа долоон төрлийн жимс хурааж байна л даа. Алим, үхрийн нүд, чацаргана, бөөрөлзгөнө гэх жишээтэй",
                "role_context": "Хөдөө аж ахуй ба туршилт",
                "tags": ["жимс_тариалалт", "хөдөө_аж_ахуй", "туршилт"],
            },
            {
                "fact": "Нутгийн ургамлыг говьд нь нутагшуулах чиглэлээр Ханбогдын Мандал-Овоогийн хайлаас, Зүүнсайхан уулын Улиастайн-Амын зэрлэг говийн улиас зэргийг амжилттай үржүүлэн суулгасан.",
                "source_quote": "Ханбогдын Мандал-Овоогийн хайлаасыг авчирч тарьсан нь сайхан ургасан даа. Манай хайлаас бол том уст хайлаасны ангилалд багтдаг",
                "role_context": "Мод үржүүлгийн арга барил",
                "tags": ["ургамал_судлал", "нутгийн_мод", "экологи"],
            },
            {
                "fact": "Хайлаас мод 50 метр, говийн сухай 15 метр хүртэл гүн үндэслэж хөрсний усанд хүрч бие даан ургадаг болохыг практикт хэрэгжүүлсэн.",
                "source_quote": "хайлаас модыг 50 метр гүн үндэслэнэ гэсэн байна лээ. Манай говийн сухай бол лав 15 метр гүн үндэслэдэг",
                "role_context": "Экологийн туршлага",
                "tags": ["байгаль_хамгаалал", "судалгаа", "цөлжилт"],
            },
            {
                "fact": "Үр хүүхдүүд, гэр бүл нь булгийн усны услалтын систем, хашаа хороо барихад санхүүгийн болон биеийн хүчний туслалцаа үзүүлж дэмждэг.",
                "source_quote": "Манай хүүхдүүд таван төгрөг олсон ч илүү гарах юм байдаг бол энэ булаг усныхаа услалтын системийн үйл ажиллагаанд нэмэрлэнэ гэдэг",
                "role_context": "Гэр бүлийн дэмжлэг",
                "tags": ["гэр_бүл", "дэмжлэг"],
            },
            {
                "fact": "Д.Бараадуузын төрсөн эцэг нь эрдэм боловсролтой лам хүн байсан ба 1940-өөд онд лам нарыг хар болгоход хөдөө гарч гэр бүл болоход төрсөн.",
                "source_quote": "Миний аав эрдэм боловсролтой лам хүн байсан. 1921 оны хувьсгал гараад, 1940-өөд он болж лам нарыг хар болгож эхлэхэд хөдөө гарч, хар хүн болоод авгай авахад төрсөн хүүхэд нь би юм",
                "role_context": "Удам угсаа ба бага нас",
                "tags": ["удам_угсаа", "намтар"],
            },
            {
                "fact": "Түүнийг аавынх нь төрсөн дүү (нагац ах) Дэмчиг үрчилж авч өсгөсөн тул Дэмчигийн Бараадууз гэж нэрлэгдэх болсон.",
                "source_quote": "Намайг Дэмчигийн Бараадууз гэдэг. Аавын минь төрсөн дүү намайг үрчилж авсан юм",
                "role_context": "Овог нэр",
                "tags": ["гэр_бүл", "намтар"],
            },
            {
                "fact": "Өмнөговь аймгийн төвд байгуулсан 500 га хайлаасан ойн орчимд 40-50 км-ийн зайд сүүлийн 14-15 жил ган болоогүй, хур тунадас татдаг байгалийн өөрчлөлт ажиглагдсан.",
                "source_quote": "Сүүлийн 14, 15 жил 500-аад га газар хайлаасан ой байгуулахад яг энэ хайлаасан ой байгаагийн орчим хааш хаашаа 40-50 километрийн дотор ган болоогүй",
                "role_context": "Экологийн бодит үр дүн",
                "tags": ["экологи", "эерэг_нөлөө", "уур_амьсгал"],
            },
        ]

        b_facts_chron = [
            {
                "date": "1957",
                "fact": "Өмнөговь аймаг төв суурин газраараа анх мод тарьж эхэлсэн.",
                "source_quote": "Өмнөговь аймаг төв суурийн газраараа 1957 оноос эхэлж мод тарьсан",
                "role_context": "Өмнөговь аймгийн ойжуулалтын түүх",
                "tags": ["түүх", "аймаг"],
            },
            {
                "date": "1990",
                "fact": "Өмнөговь аймагт мод тарих үйл ажиллагаа эрчимжсэн.",
                "source_quote": "Тэгээд 1990-ээд оноос эрчимжсэн юм",
                "role_context": "Ойжуулалтын эрчимжилт",
                "tags": ["түүх", "ойжуулалт"],
            },
            {
                "date": "1991",
                "fact": "Монгол Улсын их сургуулийн курст сууж байхад ойн тэнхимийн эрхлэгч н.Гомбосүрэн түүнд нутгийн ургамал өөрийн бүсээс 60 км радиуст эрсдэлгүй ургадаг технологийн чухал зөвлөгөөг өгсөн.",
                "source_quote": "Би гучин жилийн өмнө Монгол Улсын их сургуульд нэг курст суусан юм. Тэгэхэд их сургуулийн ойн тэнхимийн эрхлэгч н.Гомбосүрэн гэж агуу сайхан хүн байлаа",
                "role_context": "Ойн технологийн сургалт",
                "tags": ["боловсрол", "багш", "сургалт"],
            },
            {
                "date": "1992",
                "fact": "Д.Бараадууз Өмнөговь аймагт нутагтаа мод тарьж, мод үржүүлгийн газар байгуулах ажлаа эхлүүлсэн.",
                "source_quote": "Тэрбээр 1992 оноос хойш Өмнөговь аймагт мод тарьж, мод үржүүлгийн газар байгуулснаас",
                "role_context": "Мод тарих гараа",
                "tags": ["гараа", "эхлэл", "мод_үржүүлэг"],
            },
            {
                "date": "1995",
                "fact": "ХААЯ-д услалтын системийн төсөл өгч Засгийн газраас 9 сая төгрөгийн буцалтгүй тусламж авч, тал хөрөнгийг өөрөө хариуцан 6 га талбайд мод, ногоо, малын тэжээл тариалсан.",
                "source_quote": "Нэг удаа ХААЯ-д услалтын системийн төсөл өгч, яамнаас тал хөрөнгийг нь, өөрөө талыг нь хариуцаад зургаан га газар мод ногоо, малын тэжээлийн ургамал тариалсан. Төслөө хийхэд Засгаас есөн сая төгрөгийн буцалтгүй тусламж өгсөн юм",
                "role_context": "Услалтын систем төсөл",
                "tags": ["төсөл", "услалт", "хөрөнгө_оруулалт"],
            },
            {
                "date": "1998",
                "fact": "Услалтын системийн төсөл хэрэгжүүлсний гурав дахь жилдээ аймгийн аварга цол хүртсэн.",
                "source_quote": "Үүний дараа би гурав дахь жил дээрээ аймгийн аварга болоод",
                "role_context": "Шагнал амжилт",
                "tags": ["амжилт", "шагнал"],
            },
            {
                "date": "2001",
                "fact": "Услалтын системийн төслийн зургаа дахь жил дээрээ ХААЯ-ны системийн Малын тэжээлийн бэлтгэлтийн аварга болсон.",
                "source_quote": "зургаа дахь жил дээрээ ХААЯ-ны системийн Малын тэжээлийн бэлтгэлтийн аварга болсон",
                "role_context": "Салбарын шагнал",
                "tags": ["амжилт", "ХААЯ", "шагнал"],
            },
            {
                "date": "2006",
                "fact": "Өмнөговь аймагт хэрэгжсэн “Ногоон хэрэм” төсөлд 27 мянган хайлаас мод нийлүүлж аймгийн төвийн 500 га ойжуулалтын ажлыг дэмжсэн.",
                "source_quote": "Өмнөговь аймагт ойжуулалтын “Ногоон хэрэм” төсөл хэрэгжсэн юм. Тэр төсөл надаас 27 мянган хайлаас мод авч тарьсан",
                "role_context": "Ногоон хэрэм төслийн нийлүүлэлт",
                "tags": ["Ногоон_хэрэм", "мод_нийлүүлэлт", "ойжуулалт"],
            },
            {
                "date": "2021-05",
                "fact": "Монголын говийг ойжуулах их үйлсэд оруулсан онцгой хувь нэмрийг үнэлж Монгол Улсын Хөдөлмөрийн баатар цол хүртээсэн.",
                "source_quote": "Монголын говийг ойжуулах их үйлсээ төр түмэндээ үнэлүүлж Хөдөлмөрийн баатар болсонд тань баяр хүргэе",
                "role_context": "Төрийн дээд шагнал",
                "tags": ["Хөдөлмөрийн_баатар", "төрийн_шагнал"],
            },
            {
                "date": "2021-07-20",
                "fact": "Эргэлт.мн сайтад 30 жилийн говийн ойжуулалтын туршлага, говийн модны онцлог болон үр дүнгийн талаар дэлгэрэнгүй ярилцлага өгсөн.",
                "source_quote": "Элсэн говьд олон мянган мод тарьж, эх дэлхийгээ энэрэн хайрлах ухааныг дэлгэрүүлж яваа Монгол Улсын Хөдөлмөрийн баатар, Байгаль орчны гавьяат Д.Бараадууз гуайтай ярилцлаа",
                "role_context": "Хэвлэлийн ярилцлага",
                "tags": ["ярилцлага", "хэвлэл"],
            },
        ]

        b_rels = [
            {
                "target_name": "Хөдөө аж ахуйн яам",
                "rel_type": "хамтран ажиллагч / төсөл хэрэгжүүлэгч",
                "target_kind": "org",
                "start_date": "1995",
                "source_quote": "Нэг удаа ХААЯ-д услалтын системийн төсөл өгч, яамнаас тал хөрөнгийг нь, өөрөө талыг нь хариуцаад зургаан га газар мод ногоо, малын тэжээлийн ургамал тариалсан",
            },
            {
                "target_name": "Ногоон хэрэм төсөл",
                "rel_type": "мод нийлүүлэгч хамтрагч",
                "target_kind": "org",
                "start_date": "2006",
                "source_quote": "Өмнөговь аймагт ойжуулалтын “Ногоон хэрэм” төсөл хэрэгжсэн юм. Тэр төсөл надаас 27 мянган хайлаас мод авч тарьсан",
            },
            {
                "target_name": "Өмнөговь аймаг",
                "rel_type": "үйл ажиллагааны гол нутаг",
                "target_kind": "location",
                "start_date": "1992",
                "source_quote": "1992 оноос хойш Өмнөговь аймагт мод тарьж, мод үржүүлгийн газар байгуулснаас",
            },
            {
                "target_name": "Монгол Улсын их сургууль",
                "rel_type": "суралцагч",
                "target_kind": "school",
                "start_date": "1991",
                "source_quote": "Би гучин жилийн өмнө Монгол Улсын их сургуульд нэг курст суусан юм",
            },
            {
                "target_name": "Гомбосүрэн",
                "rel_type": "багш / зөвлөгч (МУИС-ийн Ойн тэнхимийн эрхлэгч)",
                "target_kind": "person",
                "start_date": "1991",
                "source_quote": "их сургуулийн ойн тэнхимийн эрхлэгч н.Гомбосүрэн гэж агуу сайхан хүн байлаа",
            },
        ]

        # Verify all quotes exist in selected_text
        for item in b_facts_bio:
            verify_substring(item["source_quote"], s1_selected_text, "Baraaduuz Bio")
        for item in b_facts_chron:
            verify_substring(item["source_quote"], s1_selected_text, "Baraaduuz Chron")
        for item in b_rels:
            verify_substring(item["source_quote"], s1_selected_text, "Baraaduuz Rel")

        # Save facts to DB
        added_b = 0
        for item in b_facts_bio:
            ex = db.query(models.Fact).filter(
                models.Fact.entity_id == baraaduuz.id,
                models.Fact.fact_type == "biographical",
                models.Fact.fact_text == item["fact"],
            ).first()
            if not ex:
                fact = models.Fact(
                    entity_id=baraaduuz.id,
                    source_id=source1.id,
                    fact_type="biographical",
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    sentiment_score=1.0,
                )
                fact.tags = item["tags"]
                db.add(fact)
                importing.assign_fact_id(db, fact)
                added_b += 1

        for item in b_facts_chron:
            fact_date, precision, date_end = parse_flexible_date(item["date"])
            ex = db.query(models.Fact).filter(
                models.Fact.entity_id == baraaduuz.id,
                models.Fact.fact_type == "chronological",
                models.Fact.fact_text == item["fact"],
            ).first()
            if not ex:
                fact = models.Fact(
                    entity_id=baraaduuz.id,
                    source_id=source1.id,
                    fact_type="chronological",
                    fact_date=fact_date,
                    date_precision=precision,
                    fact_date_end=date_end,
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    sentiment_score=1.0,
                )
                fact.tags = item["tags"]
                db.add(fact)
                importing.assign_fact_id(db, fact)
                added_b += 1

        for rel in b_rels:
            rel_start, start_prec, _ = parse_flexible_date(rel.get("start_date"))
            ex_r = db.query(models.Relationship).filter(
                models.Relationship.source_entity_id == baraaduuz.id,
                models.Relationship.target_name == rel["target_name"],
                models.Relationship.rel_type == rel["rel_type"],
            ).first()
            if not ex_r:
                r_obj = models.Relationship(
                    source_entity_id=baraaduuz.id,
                    source_id=source1.id,
                    target_name=rel["target_name"],
                    target_entity_id=None,
                    rel_type=rel["rel_type"],
                    target_kind=rel.get("target_kind"),
                    start_date=rel_start,
                    start_precision=start_prec,
                    source_quote=rel.get("source_quote"),
                )
                db.add(r_obj)

        db.commit()
        print(f"Added {added_b} facts and {len(b_rels)} relationships for Д.Бараадууз.")

        # =========================================================================
        # 2. E-MONGOLIA (Цахим үйлчилгээний нэгдсэн систем)
        # =========================================================================
        print("\n>>> Ingesting Entity 2: E-Mongolia...")
        emongolia = db.query(models.Entity).filter(models.Entity.name == "И-Монголиа").first()
        if not emongolia:
            emongolia = db.query(models.Entity).filter(models.Entity.name == "E-Mongolia").first()
        if not emongolia:
            emongolia = models.Entity(
                name="E-Mongolia",
                entity_type="org",
                description="Төрийн үйлчилгээний нэгдсэн систем. Төрийн байгууллагуудын хүнд суртал, авлига, цаасны зардлыг халж, иргэдэд төрийн үйлчилгээг түргэн шуурхай цахимаар хүргэх зорилготой платформ.",
                tldr_summary="Төрийн 1000+ үйлчилгээг цахимжуулж, иргэдийн цаг, зардлыг ихээхэн хэмнэсэн нэгдсэн систем.",
                is_stub=False,
            )
            db.add(emongolia)
            db.flush()

            for al, kd in [
                ("И-Монголиа", "spelling"),
                ("e-Mongolia", "spelling"),
                ("И-Монгол", "nickname"),
                ("Цахим үйлчилгээний нэгдсэн систем", "other"),
            ]:
                alias_norm = al.lower().strip()
                db.add(models.EntityAlias(entity_id=emongolia.id, alias=al, alias_norm=alias_norm, kind=kd))
            db.flush()
            print(f"Created Entity: {emongolia.name} (id={emongolia.id})")
        else:
            print(f"Found Existing Entity: {emongolia.name} (id={emongolia.id})")

        # Source 2: Ikon.mn launch article
        s2_url = "https://ikon.mn/n/202j"
        s2_title = "Төрийн 181 үйлчилгээг нэг дор төвлөрүүлж, цахимжуулсан E-Mongolia нэгдсэн системийг танилцууллаа"
        source2 = db.query(models.Source).filter(models.Source.url == s2_url).first()

        scraped2 = scraper.scrape(s2_url)
        # We select the actual article body blocks (indices 8, 10, 11, 12, 13)
        b2_candidates = [
            b["text"].strip() for b in scraped2.get("blocks", [])
            if any(k in b["text"] for k in [
                "Үндэсний цахим үйлчилгээний E-Mongolia",
                "Эхний шатанд сангийн яамны Ebarimt",
                "Үүнтэй холбогдуулж өнөөдөр E-Mongolia системийг",
                "Иргэд гар утаснаасаа E-Mongolia аппликэшнийг",
                "Төрийн байгууллагууд цахим шилжилт хийснээр",
            ])
        ]
        s2_selected_text = "\n\n".join(b2_candidates)

        if not source2:
            source2 = models.Source(
                source_type="article",
                category="media",
                url=s2_url,
                title=s2_title,
                author="Т.Саран, iKon.mn",
                publication_date=parse_flexible_date("2020-10-02")[0],
                cleaned_text=s2_selected_text,
                selected_text=s2_selected_text,
                raw_hash=stable_hash(s2_selected_text),
                sha256_hash=stable_hash(s2_selected_text),
                bias_score=0.8,
                reliability_score=0.95,
            )
            db.add(source2)
            db.flush()
            print(f"Created Source 2: {source2.title} (id={source2.id})")
        else:
            print(f"Found Existing Source 2: (id={source2.id})")

        # Facts for E-Mongolia
        e_facts_bio = [
            {
                "fact": "Төрийн үйлчилгээг нэг цонхонд төвлөрүүлсэн олон улсын жишгийг Монгол Улсын Засгийн газар нэвтрүүлсэн төсөл юм.",
                "source_quote": "төрийн үйлчилгээг нэг цонхонд төвлөрүүлсэн олон улсын жишгийг Монгол Улсын Засгийн газар нэвтрүүлж байгааг",
                "role_context": "Системийн зорилго ба жишиг",
                "tags": ["цахим_шилжилт", "төрийн_үйлчилгээ", "эерэг_нөлөө"],
            },
            {
                "fact": "Үүрэн холбооны оператор компаниуд (Мобиком, Юнител, Скайтел, Жи-Мобайл) нийгмийн хариуцлагын хүрээнд E-Mongolia аппликэшнийг ашиглахад дата хураамж авахгүй хамтран ажилласан.",
                "source_quote": "Иргэд гар утаснаасаа E-Mongolia аппликэшнийг ашиглахад дата унахгүй бөгөөд үүрэн холбооны Мобиком, Юнител, Скайтел, Жи-Мобайл оператор компаниуд энэ тал дээр нийгмийн хариуцлагын хүрээнд хамтран ажиллаж байгаа",
                "role_context": "Дата үнэгүй үйлчилгээ",
                "tags": ["хүртээмж", "хамтын_ажиллагаа", "оператор"],
            },
            {
                "fact": "Төрийн байгууллагууд цахим шилжилт хийснээр бичиг хэрэг, шуудангийн зардлаас жилдээ хамгийн багадаа 10 тэрбум төгрөг хэмнэх боломж бүрдсэн.",
                "source_quote": "Төрийн байгууллагууд цахим шилжилт хийснээр бичиг хэрэг, шуудангийн зардлаас жилдээ хамгийн багадаа 10 тэрбум төгрөгийг хэмнэх боломжтой",
                "role_context": "Төсвийн хэмнэлт",
                "tags": ["төсөв", "хэмнэлт", "үр_өгөөж"],
            },
            {
                "fact": "Иргэдийн хувьд төрийн үйлчилгээг цахимаар авснаар жилдээ 3.7 тэрбум төгрөг болон мөнгөөр хэмжигдэхгүй цаг хугацааг хэмнэх тооцоолол гарсан.",
                "source_quote": "иргэдийн хувьд 3.7 тэрбум төгрөгийг хэмнэх тооцоолол гарчээ. Улсын төсөв, хувь хүний санхүүг хэмнэхээс гадна мөнгөөр хэмжигдэхгүй цаг хугацааг Монгол Улсын иргэн бүрд хэмнэж өгөх давуу талтайг",
                "role_context": "Иргэдийн эдийн засаг, цаг хэмнэлт",
                "tags": ["иргэдийн_хэмнэлт", "цаг_хэмнэлт", "үр_дүн"],
            },
            {
                "fact": "Төрийн үйлчилгээг цахимжуулах ажил нь нэг Засгийн газар бус хэд хэдэн Засгийн газар дамжин хийгдсэн урт хугацааны төсөл юм.",
                "source_quote": "Төрийн үйлчилгээг цахимжуулах ажлыг нэг Засгийн газар бус хэд хэдэн Засгийн газар дамжин хийгдэж өнөөдөр эхний ээлжинд бэлэн болоод байна",
                "role_context": "Бодлогын залгамж чанар",
                "tags": ["залгамж_чанар", "төрийн_бодлого"],
            },
        ]

        e_facts_chron = [
            {
                "date": "2020-10-01",
                "fact": "Үндэсний цахим үйлчилгээний E-Mongolia нэгдсэн системийг Харилцаа холбоо, мэдээллийн технологийн газраас хэрэглэгчдэд албан ёсоор хүргэж эхэлсэн.",
                "source_quote": "Үндэсний цахим үйлчилгээний E-Mongolia нэгдсэн системийг энэ сарын 1-нээс эхлэн Харилцаа холбоо, мэдээллийн технологийн газраас хэрэглэгчдэд хүргэж эхэллээ",
                "role_context": "Системийн нээлт",
                "tags": ["нээлт", "эхлэл", "ХХМТГ"],
            },
            {
                "date": "2020-10-02",
                "fact": "E-Mongolia системийг танилцуулах хэвлэлийн бага хурал болж, ЗГХЭГ-ын дарга Л.Оюун-Эрдэнэ болон холбогдох албаныхан оролцсон.",
                "source_quote": "Үүнтэй холбогдуулж өнөөдөр E-Mongolia системийг танилцуулах хэвлэлийн бага хурлыг зохион байгуулсан бөгөөд ЗГХЭГ-ын дарга Л.Оюун-Эрдэнэ оролцлоо",
                "role_context": "Албан ёсны танилцуулга",
                "tags": ["танилцуулга", "хэвлэлийн_хурал"],
            },
            {
                "date": "2020-10",
                "fact": "Эхний шатанд Сангийн яамны Ebarimt, ХНХЯ-ны Ehalamj болон иргэний үнэмлэх, гэр бүлийн, тээврийн хэрэгслийн лавлагаа зэрэг төрийн 181 үйлчилгээг нэг цонхонд амжилттай төвлөрүүлж цахимжуулсан.",
                "source_quote": "Эхний шатанд сангийн яамны Ebarimt, Хөдөлмөр нийгмийн хамгааллын яамны Ehalamj зэрэг төрийн цахим порталуудаас гадна иргэний үнэмлэх, гэр бүлийн, тээврийн хэрэгслэлийн лавлагаа зэрэг төрийн 181 үйлчилгээг нэг цонхонд богино хугацаанд амжилттай төвлөрүүлж, цахимжуулжээ",
                "role_context": "Эхний ээлжийн 181 үйлчилгээ",
                "tags": ["үйлчилгээ", "Ebarimt", "Ehalamj"],
            },
            {
                "date": "2020-10",
                "fact": "Цаашид төрөөс цахим хэлбэрээр үзүүлж буй нийт 492 үйлчилгээг нэг систем, нэг дэд бүтцэд бүрэн нэгтгэх зорилт тавьсан.",
                "source_quote": "цаашид төрөөс цахим хэлбэрээр үзүүлж буй нийтдээ 492 үйлчилгээг нэг систем, нэг дэд бүтцэд нэгтгэнэ",
                "role_context": "Хөгжүүлэлтийн зорилт",
                "tags": ["төлөвлөгөө", "зорилт"],
            },
        ]

        # Link Oyun-Erdene (entity 15) to E-Mongolia
        oyunerdene = db.query(models.Entity).filter(models.Entity.name == "Лувсаннамсрайн Оюун-Эрдэнэ").first()
        oe_id = oyunerdene.id if oyunerdene else None

        e_rels = [
            {
                "target_name": "Харилцаа холбоо, мэдээллийн технологийн газар",
                "rel_type": "хэрэгжүүлэгч төрийн агентлаг",
                "target_kind": "org",
                "start_date": "2020-10-01",
                "source_quote": "Харилцаа холбоо, мэдээллийн технологийн газраас хэрэглэгчдэд хүргэж эхэллээ",
            },
            {
                "target_name": "Лувсаннамсрайн Оюун-Эрдэнэ",
                "rel_type": "санаачлагч / танилцуулагч (ЗГХЭГ-ын дарга)",
                "target_kind": "person",
                "start_date": "2020-10-02",
                "source_quote": "ЗГХЭГ-ын дарга Л.Оюун-Эрдэнэ оролцлоо",
                "target_entity_id": oe_id,
            },
            {
                "target_name": "Мобиком",
                "rel_type": "хамтрагч оператор (тэг дата)",
                "target_kind": "company",
                "start_date": "2020-10",
                "source_quote": "үүрэн холбооны Мобиком, Юнител, Скайтел, Жи-Мобайл оператор компаниуд энэ тал дээр нийгмийн хариуцлагын хүрээнд хамтран ажиллаж байгаа",
            },
            {
                "target_name": "Юнител",
                "rel_type": "хамтрагч оператор (тэг дата)",
                "target_kind": "company",
                "start_date": "2020-10",
                "source_quote": "үүрэн холбооны Мобиком, Юнител, Скайтел, Жи-Мобайл оператор компаниуд энэ тал дээр нийгмийн хариуцлагын хүрээнд хамтран ажиллаж байгаа",
            },
            {
                "target_name": "Скайтел",
                "rel_type": "хамтрагч оператор (тэг дата)",
                "target_kind": "company",
                "start_date": "2020-10",
                "source_quote": "үүрэн холбооны Мобиком, Юнител, Скайтел, Жи-Мобайл оператор компаниуд энэ тал дээр нийгмийн хариуцлагын хүрээнд хамтран ажиллаж байгаа",
            },
            {
                "target_name": "Жи-Мобайл",
                "rel_type": "хамтрагч оператор (тэг дата)",
                "target_kind": "company",
                "start_date": "2020-10",
                "source_quote": "үүрэн холбооны Мобиком, Юнител, Скайтел, Жи-Мобайл оператор компаниуд энэ тал дээр нийгмийн хариуцлагын хүрээнд хамтран ажиллаж байгаа",
            },
        ]

        for item in e_facts_bio:
            verify_substring(item["source_quote"], s2_selected_text, "EMongolia Bio")
        for item in e_facts_chron:
            verify_substring(item["source_quote"], s2_selected_text, "EMongolia Chron")
        for item in e_rels:
            verify_substring(item["source_quote"], s2_selected_text, "EMongolia Rel")

        added_e = 0
        for item in e_facts_bio:
            ex = db.query(models.Fact).filter(
                models.Fact.entity_id == emongolia.id,
                models.Fact.fact_type == "biographical",
                models.Fact.fact_text == item["fact"],
            ).first()
            if not ex:
                fact = models.Fact(
                    entity_id=emongolia.id,
                    source_id=source2.id,
                    fact_type="biographical",
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    sentiment_score=0.9,
                )
                fact.tags = item["tags"]
                db.add(fact)
                importing.assign_fact_id(db, fact)
                added_e += 1

        for item in e_facts_chron:
            fact_date, precision, date_end = parse_flexible_date(item["date"])
            ex = db.query(models.Fact).filter(
                models.Fact.entity_id == emongolia.id,
                models.Fact.fact_type == "chronological",
                models.Fact.fact_text == item["fact"],
            ).first()
            if not ex:
                fact = models.Fact(
                    entity_id=emongolia.id,
                    source_id=source2.id,
                    fact_type="chronological",
                    fact_date=fact_date,
                    date_precision=precision,
                    fact_date_end=date_end,
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    sentiment_score=0.9,
                )
                fact.tags = item["tags"]
                db.add(fact)
                importing.assign_fact_id(db, fact)
                added_e += 1

        for rel in e_rels:
            rel_start, start_prec, _ = parse_flexible_date(rel.get("start_date"))
            ex_r = db.query(models.Relationship).filter(
                models.Relationship.source_entity_id == emongolia.id,
                models.Relationship.target_name == rel["target_name"],
                models.Relationship.rel_type == rel["rel_type"],
            ).first()
            if not ex_r:
                r_obj = models.Relationship(
                    source_entity_id=emongolia.id,
                    source_id=source2.id,
                    target_name=rel["target_name"],
                    target_entity_id=rel.get("target_entity_id"),
                    rel_type=rel["rel_type"],
                    target_kind=rel.get("target_kind"),
                    start_date=rel_start,
                    start_precision=start_prec,
                    source_quote=rel.get("source_quote"),
                )
                db.add(r_obj)

        db.commit()
        print(f"Added {added_e} facts and {len(e_rels)} relationships for E-Mongolia.")

        print("\nAll positive facts and entities successfully ingested!")

    finally:
        db.close()


if __name__ == "__main__":
    ingest()
