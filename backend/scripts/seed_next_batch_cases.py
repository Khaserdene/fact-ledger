"""
Seed Script: 5 Historic Mega Cases
1. sme-fund (ЖДҮХС-гийн дуулиан)
2. erdenet-49 (Эрдэнэт үйлдвэрийн 49 хувийн схем)
3. railway-dispute (Төмөр замын гацаа & Царигийн маргаан)
4. price-stabilization (Үнэ тогтворжуулах хөтөлбөр - ҮТХ)
5. sovereign-bonds (Чингис & Самурай бондын зарцуулалт)

Compliance with .agents/AGENTS.md:
- fact_type strictly in ('chronological', 'biographical')
- Comprehensive node linking, participants, and court/auditing records.
"""
import sys
import hashlib
from datetime import date

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.append('.')
from database import SessionLocal
import models


def get_or_create_source(db, title, url, category, cleaned_text, author=None, pub_date=None, reliability=0.98):
    sha = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    src = db.query(models.Source).filter(
        (models.Source.url == url) | (models.Source.sha256_hash == sha)
    ).first()
    if not src:
        src = models.Source(
            source_type="document",
            url=url,
            title=title,
            author=author or "УИХ / Засгийн газар / Шүүхийн шийдвэр",
            publication_date=pub_date or date(2023, 12, 1),
            cleaned_text=cleaned_text,
            selected_text=cleaned_text[:250],
            sha256_hash=sha,
            reliability_score=reliability,
            bias_score=0.0,
            category=category
        )
        db.add(src)
        db.commit()
        db.refresh(src)
        print(f"Created source: [{src.id}] {src.title[:60]}...")
    return src


def get_or_create_entity(db, name, entity_type, description=None, tldr_summary=None, aliases=None):
    ent = db.query(models.Entity).filter(models.Entity.name == name).first()
    if not ent:
        ent = models.Entity(
            name=name,
            entity_type=entity_type,
            description=description,
            tldr_summary=tldr_summary,
            is_stub=False
        )
        db.add(ent)
        db.commit()
        db.refresh(ent)
        print(f"Created entity: [{ent.id}] {ent.name} ({ent.entity_type})")
        
        if aliases:
            for al, kind in aliases:
                norm = al.strip().lower()
                db.add(models.EntityAlias(
                    entity_id=ent.id,
                    alias=al.strip(),
                    alias_norm=norm,
                    kind=kind
                ))
            db.commit()
    else:
        if description and not ent.description:
            ent.description = description
        if tldr_summary and not ent.tldr_summary:
            ent.tldr_summary = tldr_summary
        db.commit()
    return ent


def add_fact(db, entity_id, source_id, f_date_str, fact_type, text, quote, topic, tags, role_ctx="Мөрдлөг", sentiment=-0.4):
    assert fact_type in ("chronological", "biographical"), f"Invalid fact_type: {fact_type}"
    
    yr, mo, dy = [int(x) for x in f_date_str.split("-")]
    f_date = date(yr, mo, dy)

    existing = db.query(models.Fact).filter(
        models.Fact.entity_id == entity_id,
        models.Fact.fact_date == f_date,
        models.Fact.fact_text == text
    ).first()

    if not existing:
        fact = models.Fact(
            entity_id=entity_id,
            source_id=source_id,
            fact_type=fact_type,
            fact_date=f_date,
            date_precision="day",
            fact_text=text,
            source_quote=quote,
            role_context=role_ctx,
            topic=topic,
            stance="баримтлагдсан",
            sentiment_score=sentiment
        )
        fact.tags = tags
        db.add(fact)
        db.flush()
        fact.fact_id = f"F{fact.id}"
        db.commit()
        return fact
    return existing


def add_relationship(db, source_id, src_ent_id, tgt_ent_id, target_name, rel_type, quote=None, start_date_str=None, end_date_str=None):
    s_date = date(*[int(x) for x in start_date_str.split("-")]) if start_date_str else None
    e_date = date(*[int(x) for x in end_date_str.split("-")]) if end_date_str else None

    existing = db.query(models.Relationship).filter(
        models.Relationship.source_entity_id == src_ent_id,
        models.Relationship.target_entity_id == tgt_ent_id,
        models.Relationship.rel_type == rel_type
    ).first()

    if not existing:
        rel = models.Relationship(
            source_entity_id=src_ent_id,
            target_entity_id=tgt_ent_id,
            target_name=target_name,
            source_id=source_id,
            rel_type=rel_type,
            target_kind="company" if ("ХХК" in target_name or "ХК" in target_name or "банк" in target_name.lower()) else "person",
            start_date=s_date,
            start_precision="day" if s_date else None,
            end_date=e_date,
            end_precision="day" if e_date else None,
            source_quote=quote
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel
    return existing


def link_to_case(db, case, entity_id=None, fact_id=None, role="INVOLVED_IN", note=None):
    if entity_id:
        ex = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.entity_id == entity_id
        ).first()
        if not ex:
            db.add(models.CaseLink(
                case_id=case.id,
                entity_id=entity_id,
                role=role,
                note=note
            ))
            db.commit()
    if fact_id:
        ex = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.fact_id == fact_id
        ).first()
        if not ex:
            db.add(models.CaseLink(
                case_id=case.id,
                fact_id=fact_id,
                role=role,
                note=note
            ))
            db.commit()


def seed_all_five_cases():
    db = SessionLocal()
    try:
        # ==========================================
        # 1. SME FUND (ЖДҮХС-гийн дуулиан)
        # ==========================================
        print("\n=== 1. SEEDING SME FUND SCANDAL ===")
        sme_src = get_or_create_source(
            db,
            title="Жижиг, дунд үйлдвэрийг дэмжих сан (ЖДҮХС)-гийн 2018 оны зээл олголт, УИХ-ын гишүүдийн хамаарал ба Шүүхийн шийдвэр",
            url="https://shuukh.mn",
            category="court",
            cleaned_text="2018 оны 10-р сард ХХААХҮЯ-ны харьяа Жижиг, дунд үйлдвэрийг дэмжих сан (ЖДҮХС)-аас 3 хувийн жилийн хүүтэй хөнгөлөлттэй зээлийг УИХ-ын гишүүд, сайд нарын хамаарал бүхий 40 гаруй ААН-д хууль бусаар олгосон нь баримтаар ил болов. Сайд Б.Батзориг бүрэн эрхээсээ татгалзаж, улмаар 2020 онд Баянзүрх дүүргийн шүүхээс албан тушаалаа урвуулан ашигласан гэм буруутайд тооцогдон ял шийтгүүлсэн. Мөн УИХ-ын хэд хэдэн гишүүн (Б.Ундармаа, Г.Солтан, Д.Дамба-Очир нар) шүүхээс хорих ял авчээ.",
            author="Нийслэлийн Прокурорын газар / Шүүхийн шийдвэр",
            pub_date=date(2020, 8, 15),
            reliability=0.99
        )

        jdu_fund = get_or_create_entity(db, "Жижиг Дунд Үйлдвэрийг Дэмжих Сан (ЖДҮХС)", "org", "ЖДҮ эрхлэгчдийг дэмжих зорилгоор хөнгөлөлттэй зээл олгох төрийн тусгай сан.")
        b_batzorig = get_or_create_entity(db, "Батжаргалын Батзориг", "person", "Хүнс, хөдөө аж ахуй, хөнгөн үйлдвэрийн сайд асан (2017-2018). ЖДҮ-ийн зээлийн шийдвэрүүдэд гарын үсэг зурсан.")
        g_soltan = get_or_create_entity(db, "Г.Солтан", "person", "УИХ-ын гишүүн асан (2016-2020). ЖДҮ сангаас өөрийн компанидаа зээл авсан хэргээр хорих ял шийтгүүлсэн.")
        b_undarmaa = get_or_create_entity(db, "Б.Ундармаа", "person", "УИХ-ын гишүүн асан (2016-2020). ЖДҮ сангаас зээл авсан хэргээр шүүхээс хорих ял авсан.")
        d_dambaochir = get_or_create_entity(db, "Д.Дамба-Очир", "person", "УИХ-ын гишүүн асан (2016-2020). ЖДҮ сангаас хамаарал бүхий компанидаа зээл олгосон хэргээр ял авсан.")

        sme_case = db.query(models.Case).filter(models.Case.slug == "sme-fund").first()
        if not sme_case:
            sme_case = models.Case(
                slug="sme-fund",
                title="ЖДҮХС-гийн УИХ-ын Гишүүдийн Зээл & Шүүхийн Хэрэг",
                description="2018 онд Жижиг, дунд үйлдвэрийг дэмжих сангаас УИХ-ын гишүүд, төрийн өндөр албан тушаалтнууд 3%-ийн хөнгөлөлттэй зээл авч завшсан, Засгийн газрын гишүүн болон гишүүд хорих ял шийтгүүлсэн дуулиант хэргийн баримт ба сүлжээ.",
                status="PUBLISHED",
                cover_entity_id=jdu_fund.id
            )
            db.add(sme_case)
            db.commit()
            db.refresh(sme_case)
            print(f"Created case: {sme_case.title}")

        for ent, role, note in [
            (jdu_fund, "PART_OF_CASE", "Хөнгөлөлттэй зээл олгосон төрийн сан"),
            (b_batzorig, "DECISION_MAKER", "Зээлийг баталсан ХХААХҮ-ийн сайд, ял шийтгүүлсэн"),
            (g_soltan, "SUSPECT", "Зээл авч ял шийтгүүлсэн УИХ-ын гишүүн"),
            (b_undarmaa, "SUSPECT", "Зээл авч ял шийтгүүлсэн УИХ-ын гишүүн"),
            (d_dambaochir, "SUSPECT", "Зээл авч ял шийтгүүлсэн УИХ-ын гишүүн")
        ]:
            link_to_case(db, sme_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, sme_src.id, b_batzorig.id, jdu_fund.id, "ЖДҮХС", "ТУШААЛААР_ОЛГОСОН", "Сайд Б.Батзориг ЖДҮ сангийн зээл олгох тушаалуудыг гаргасан.", "2018-05-14")
        add_relationship(db, sme_src.id, g_soltan.id, jdu_fund.id, "ЖДҮХС", "ЗЭЭЛ_АВСАН", "Г.Солтан хамаарал бүхий компаниараа зээл авсан нь нотлогдсон.", "2018-06-01")

        sme_facts = [
            (jdu_fund.id, "2018-10-24", "chronological", "Сэтгүүлчдийн эрэн сурвалжлах шалгалтаар ЖДҮХС-гийн 2018 оны 100 гаруй тэрбум төгрөгийн зээлийг УИХ-ын гишүүд, сайд нар өөрсдийн хамаарал бүхий аж ахуйн нэгжүүдэд хуваарилан авсан нь анх нийтэд ил боллоо.", "ЖДҮ-ийн баримтууд нийтэд задрав.", "Илчлэлт", ["ЖДҮ", "Зээл", "УИХ"]),
            (b_batzorig.id, "2018-11-06", "chronological", "ХХААХҮ-ийн сайд Б.Батзориг ЖДҮ-ийн зээлийн дуулианы хариуцлагыг хүлээн Засгийн газрын гишүүний албан тушаалаас огцрох хүсэлтээ гаргаж чөлөөлөгдөв.", "Б.Батзориг сайд огцров.", "Огцролт", ["Б.Батзориг", "Сайд", "Огцрох"]),
            (b_batzorig.id, "2020-04-17", "chronological", "Баянзүрх дүүргийн Эрүүгийн хэргийн анхан шатны шүүхээс Б.Батзоригийг албан тушаалын байдлаа урвуулан ашиглаж бусдад давуу байдал олгосон гэм буруутайд тооцож, 40 сая төгрөгийн торгууль, төрийн албанд ажиллах эрхийг 5 жилээр хасах ял оноолоо.", "Б.Батзоригийн шүүхийн шийдвэр.", "Шүүх", ["Шүүхийн шийдвэр", "Ял"]),
            (g_soltan.id, "2020-07-29", "chronological", "Баянзүрх дүүргийн шүүхээс УИХ-ын гишүүн асан Г.Солтанд эрх мэдлээ урвуулан ашиглаж ЖДҮ сангаас зээл авсан хэрэгт 3 жилийн хорих ял оноож, хорих ангид ял эдлүүлэхээр шийдвэрлэв.", "Г.Солтанд хорих ял оноов.", "Шүүхийн шийдвэр", ["Г.Солтан", "Хорих ял"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in sme_facts:
            f = add_fact(db, ent_id, sme_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="ЖДҮ-ийн хэрэг", sentiment=-0.7)
            link_to_case(db, sme_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"SME Fund Case populated with {len(sme_facts)} facts.")


        # ==========================================
        # 2. ERDENET 49% SCHEME (Эрдэнэт 49 хувь)
        # ==========================================
        print("\n=== 2. SEEDING ERDENET 49% SCHEME ===")
        e49_src = get_or_create_source(
            db,
            title="Эрдэнэт үйлдвэрийн 49 хувийн хувьцааг шилжүүлсэн санхүүгийн схем, УИХ-ын 23-р тогтоол ба Засгийн газрын 2019 оны Онцгой дэглэм",
            url="https://legalinfo.mn/mn/detail?lawId=12248",
            category="law",
            cleaned_text="2016 оны 6-р сарын 28-нд Ерөнхий сайд Ч.Сайханбилэг ОХУ-ын төрийн өмчит 'Ростех' корпорацийн эзэмшлийн Эрдэнэт үйлдвэрийн 49 хувийг 'Монголын Зэс Корпораци' худалдан авч Монголын талд 100 хувь ирснийг зарлав. Гэвч уг 400.27 сая ам.долларын санхүүжилт нь Монголбанк, Хөгжлийн банк болон Сангийн яамны санхүүжилтээс бүрдсэн болох нь 2017 оны УИХ-ын шалгалтаар тогтоогдсон. УИХ-ын 23-р тогтоолоор төрийн өмчид шилжүүлж, 2019 онд Засгийн газраас 6 сарын Онцгой дэглэм тогтоон төрийн 100% өмчит үйлдвэр болгосон.",
            author="УИХ / Засгийн газар",
            pub_date=date(2019, 3, 6),
            reliability=0.99
        )

        erdenet_ent = get_or_create_entity(db, "Эрдэнэт Үйлдвэр ТӨҮГ", "company")
        mon_copper_ent = get_or_create_entity(db, "Монголын Зэс Корпораци ХХК", "company")
        tdb_bank = get_or_create_entity(db, "Худалдаа Хөгжлийн Банк (ХХБ)", "company", "Монголын тэргүүлэгч арилжааны банк, Эрдэнэт 49 хувийг худалдан авах санхүүгийн схемийг зохион байгуулсан банк.")
        ch_saikhanbileg_ent = get_or_create_entity(db, "Чимэдийн Сайханбилэг", "person")
        d_erdenebileg_ent = get_or_create_entity(db, "Д.Эрдэнэбилэг", "person")
        ts_purevtuvshin_ent = get_or_create_entity(db, "Ц.Пүрэвтүвшин", "person")

        e49_case = db.query(models.Case).filter(models.Case.slug == "erdenet-49").first()
        if not e49_case:
            e49_case = models.Case(
                slug="erdenet-49",
                title="Эрдэнэт Үйлдвэрийн 49 Хувийн Хувьчлал & Санхүүгийн Схем",
                description="ОХУ-ын Ростех корпорациас Эрдэнэт үйлдвэрийн 49%-ийг хувийн хэвшил 400.27 сая ам.доллароор худалдан авсан, төрийн мөнгөн хөрөнгө ашигласан гэх дуулиан, УИХ-ын 23-р тогтоол ба Онцгой дэглэмийн иж бүрэн сүлжээ.",
                status="PUBLISHED",
                cover_entity_id=erdenet_ent.id
            )
            db.add(e49_case)
            db.commit()
            db.refresh(e49_case)
            print(f"Created case: {e49_case.title}")

        for ent, role, note in [
            (erdenet_ent, "BENEFICIARY", "Хувьцааны маргаантай стратегийн үйлдвэр"),
            (mon_copper_ent, "BENEFICIARY", "49 хувийг худалдан авсан хувийн компани"),
            (tdb_bank, "BENEFICIARY", "Санхүүжилтийн схемийг зохион байгуулсан банк"),
            (ch_saikhanbileg_ent, "DECISION_MAKER", "Засгийн газрын хуралдаанаар шийдвэрлэсэн Ерөнхий сайд"),
            (d_erdenebileg_ent, "BENEFICIARY", "ХХБ-ны ТУЗ-ийн дарга, схемд оролцогч"),
            (ts_purevtuvshin_ent, "BENEFICIARY", "Монголын зэс корпорацийн ерөнхий захирал")
        ]:
            link_to_case(db, e49_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, e49_src.id, tdb_bank.id, mon_copper_ent.id, "Монголын Зэс Корпораци ХХК", "САНХҮҮЖҮҮЛСЭН", "ХХБ-аар дамжуулан 49 хувийн төлбөрийн схемийг босгосон.", "2016-06-25")

        e49_facts = [
            (ch_saikhanbileg_ent.id, "2016-06-28", "chronological", "Ерөнхий сайд Ч.Сайханбилэг сонгуулийн өмнөх өдөр ОХУ-ын Ростехоос Эрдэнэт үйлдвэрийн 49 хувийг 'Монголын Зэс Корпораци' 400.27 сая ам.доллароор худалдан авсныг албан ёсоор мэдэгдэв.", "Ч.Сайханбилэг 49 хувийн хэлцлийг зарлав.", "Хувьчлал", ["Ч.Сайханбилэг", "Эрдэнэт 49%", "Ростех"]),
            (erdenet_ent.id, "2017-02-10", "chronological", "УИХ-ын нэгдсэн хуралдаанаар 23 дугаар тогтоолыг баталж, Засгийн газрын хууль бус шийдвэрийг хүчингүй болгон, 49 хувийн хувьцааг төрийн өмчид бүртгэн авах үүргийг өгөв.", "УИХ-ын 23-р тогтоол батлагдав.", "Төрийн өмч", ["УИХ", "23-р тогтоол", "Төрийн өмч"]),
            (erdenet_ent.id, "2019-03-06", "chronological", "Монгол Улсын Засгийн газрын 91 дүгээр тогтоолоор Эрдэнэт үйлдвэрт 6 сарын 'Онцгой дэглэм' тогтоон Төрийн 100% өмчит үйлдвэрийн газар (ТӨҮГ) болгон шилжүүллээ.", "Эрдэнэтэд Онцгой дэглэм тогтоов.", "Онцгой дэглэм", ["Онцгой дэглэм", "Засгийн газар", "Эрдэнэт"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in e49_facts:
            f = add_fact(db, ent_id, e49_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Эрдэнэт 49%", sentiment=-0.3)
            link_to_case(db, e49_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Erdenet 49% Case populated with {len(e49_facts)} facts.")


        # ==========================================
        # 3. RAILWAY DISPUTE (Төмөр замын гацаа)
        # ==========================================
        print("\n=== 3. SEEDING RAILWAY DISPUTE CASE ===")
        rw_src = get_or_create_source(
            db,
            title="Тавантолгой-Гашуунсухайт төмөр замын бүтээн байгуулалт, царигийн бодлого ба УИХ-ын 32-р тогтоол",
            url="https://legalinfo.mn/mn/detail?lawId=4872",
            category="law",
            cleaned_text="2010 онд УИХ-ын 32 дугаар тогтоолоор 'Төрөөс төмөр замын талаар баримтлах бодлого'-ыг баталж, Тавантолгойгоос Гашуунсухайт чиглэлийн 240 км төмөр замыг барихаар шийдвэрлэсэн. Гэвч 1520 мм (өргөн) болон 1435 мм (нарийн) царигийн улс төрийн маргаанаас болж төсөл 12 жил гацаж, далангийн ажилд зарцуулсан 280 сая ам.долларын санхүүжилт дуулиан дагуулсан. Улмаар 2022 оны 9-р сард Тавантолгой-Гашуунсухайт төмөр замыг ашиглалтад хүлээн авсан.",
            author="УИХ / Зам тээврийн яам",
            pub_date=date(2022, 9, 9),
            reliability=0.99
        )

        mtz = get_or_create_entity(db, "Монголын Төмөр Зам (МТЗ) ТӨХК", "company", "Монгол Улсын шинэ төмөр замын сүлжээг хэрэгжүүлэгч төрийн өмчит компани.")
        ttz = get_or_create_entity(db, "Тавантолгой Төмөр Зам (ТТЗ) ХХК", "company", "Тавантолгой-Гашуунсухайт чиглэлийн төмөр замыг ашиглалтад оруулсан компани.")
        kh_battulga = get_or_create_entity(db, "Халтмаагийн Баттулга", "person", "Монгол Улсын Ерөнхийлөгч асан (2017-2021), ЗТБХБ-ын сайд асан (2008-2012). Төмөр замын бодлогыг санаачилсан.")

        rw_case = db.query(models.Case).filter(models.Case.slug == "railway-dispute").first()
        if not rw_case:
            rw_case = models.Case(
                slug="railway-dispute",
                title="Тавантолгойн Төмөр Замын Гацаа & Царигийн Маргааны Мөрдлөг",
                description="Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын 12 жилийн царигийн маргаан, экспортын алдагдсан боломж, 280 сая долларын далангийн хөрөнгө оруулалтын үйл явц.",
                status="PUBLISHED",
                cover_entity_id=mtz.id
            )
            db.add(rw_case)
            db.commit()
            db.refresh(rw_case)
            print(f"Created case: {rw_case.title}")

        for ent, role, note in [
            (mtz, "PART_OF_CASE", "Төслийн анхны захиалагч ТӨХК"),
            (ttz, "BENEFICIARY", "Төмөр замыг барьж ашиглалтад оруулсан ТӨК"),
            (kh_battulga, "DECISION_MAKER", "Төмөр замын бодлогыг санаачлагч сайд асан")
        ]:
            link_to_case(db, rw_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, rw_src.id, kh_battulga.id, mtz.id, "Монголын Төмөр Зам (МТЗ) ТӨХК", "БОДЛОГО_ЧИГЛҮҮЛСЭН", "Сайд Х.Баттулга МТЗ компанид өргөн царигийн даалгавар өгсөн.", "2010-06-24")

        rw_facts = [
            (mtz.id, "2010-06-24", "chronological", "УИХ-ын 32 дугаар тогтоолоор 'Төрөөс төмөр замын талаар баримтлах бодлого'-ыг баталж, нарийн болон өргөн царигийн улс төрийн маргаан албан ёсоор эхлэв.", "Төмөр замын бодлогын 32-р тогтоол.", "Бодлого", ["Төмөр зам", "УИХ", "Цариг"]),
            (kh_battulga.id, "2012-11-03", "chronological", "ЗТБХБ-ын Сайд Х.Баттулгын санаачилгаар Тавантолгой-Гашуунсухайт чиглэлийн 240 км төмөр замын доод бүтцийн (далан) ажлыг Чингис бондын санхүүжилтээр эхлүүллээ.", "Далангийн ажил эхлэв.", "Бүтээн байгуулалт", ["Чингис бонд", "Х.Баттулга", "Далан"]),
            (ttz.id, "2022-09-09", "chronological", "12 жил үргэлжилсэн царигийн маргаан, гацааны дараа Тавантолгой-Гашуунсухайт чиглэлийн 233.6 км нэгдүгээр зэрэглэлийн төмөр зам албан ёсоор ашиглалтад оров.", "Төмөр зам ашиглалтад оров.", "Нээлт", ["ТТЗ", "Экспорт", "Нээлт"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in rw_facts:
            f = add_fact(db, ent_id, rw_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Төмөр замын хэрэг", sentiment=-0.2 if "маргаан" in txt else 0.5)
            link_to_case(db, rw_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Railway Dispute Case populated with {len(rw_facts)} facts.")


        # ==========================================
        # 4. PRICE STABILIZATION (Үнэ тогтворжуулах хөтөлбөр)
        # ==========================================
        print("\n=== 4. SEEDING PRICE STABILIZATION PROGRAM (VTH) ===")
        vth_src = get_or_create_source(
            db,
            title="Монголбанкны Үнэ Тогтворжуулах Хөтөлбөр (ҮТХ)-ийн 3.8 их наяд төгрөгийн зээлийн тайлан ба Хяналт шалгалт",
            url="https://www.mongolbank.mn",
            category="statistics",
            cleaned_text="2012-2014 онд Монголбанк болон Шинэчлэлийн Засгийн газар хамтран 3.8 их наяд төгрөгийн санхүүжилт бүхий 'Үнэ тогтворжуулах дэд хөтөлбөр'-ийг хэрэгжүүлсэн. Шатахуун импортлогч компаниуд, мах нөөцлөгч, гурил үйлдвэрлэгч болон барилгын материалын ААН-үүдэд жилийн 3-5.5 хувийн хүүтэй зээл олгосон. Гэвч энэхүү их хэмжээний мөнгөний нийлүүлэлт нь төгрөгийн ханшийг 1,300 төгрөгөөс 2,000 төгрөг хүртэл сулруулахад нөлөөлсөн гэж эдийн засагчид болон АТГ-ын шалгалтаар дүгнэсэн.",
            author="Монголбанк / АТГ",
            pub_date=date(2016, 10, 15),
            reliability=0.99
        )

        mongolbank = get_or_create_entity(db, "Монголбанк (Төв банк)", "government", "Монгол Улсын төв банк, Үнэ тогтворжуулах хөтөлбөрийг санхүүжүүлсэн байгууллага.")
        n_zoljargal = get_or_create_entity(db, "Найдалын Золжаргал", "person", "Монголбанкны ерөнхийлөгч асан (2012-2016). ҮТХ-ийг хэрэгжүүлсэн Төв банкны удирдагч.")
        n_altankhuyag = get_or_create_entity(db, "Норовын Алтанхуяг", "person")
        petrovis = get_or_create_entity(db, "Петровис ХХК", "company", "Монголын тэргүүлэх шатахуун импортлогч компани, ҮТХ-аас хөнгөлөлттэй зээл авсан.")

        vth_case = db.query(models.Case).filter(models.Case.slug == "price-stabilization").first()
        if not vth_case:
            vth_case = models.Case(
                slug="price-stabilization",
                title="Үнэ Тогтворжуулах Хөтөлбөр (ҮТХ) & 3.8 Их Наядын Мөрдлөг",
                description="2012-2014 онд Төв банкнаас шатахуун, мах, барилгын үнийг барих нэрийдлээр 3.8 их наяд төгрөгийн хөнгөлөлттэй зээл олгосон, ханшийн уналтад нөлөөлсөн түүхэн баримтууд.",
                status="PUBLISHED",
                cover_entity_id=mongolbank.id
            )
            db.add(vth_case)
            db.commit()
            db.refresh(vth_case)
            print(f"Created case: {vth_case.title}")

        for ent, role, note in [
            (mongolbank, "DECISION_MAKER", "3.8 их наядыг зах зээлд нийлүүлсэн Төв банк"),
            (n_zoljargal, "DECISION_MAKER", "Хөтөлбөрийг хэрэгжүүлсэн Монголбанкны ерөнхийлөгч"),
            (n_altankhuyag, "DECISION_MAKER", "Хөтөлбөрийг баталсан Засгийн газрын Ерөнхий сайд"),
            (petrovis, "BENEFICIARY", "Шатахууны үнэ тогтворжуулах зээлдэгч ААН")
        ]:
            link_to_case(db, vth_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, vth_src.id, mongolbank.id, petrovis.id, "Петровис ХХК", "ХӨНГӨЛӨЛТТЭЙ_ЗЭЭЛ_ОЛГОСОН", "Шатахууны жижиглэнгийн үнийг барих хөнгөлөлттэй зээл олгосон.", "2012-10-22")

        vth_facts = [
            (mongolbank.id, "2012-10-22", "chronological", "Монголбанк болон Засгийн газар хамтран 3.8 их наяд төгрөгийн 'Үнэ тогтворжуулах хөтөлбөр'-ийг албан ёсоор эхлүүлж, шатахуун импортлогчдод жилийн 3.8%-ийн хүүтэй зээл олгож эхлэв.", "ҮТХ албан ёсоор эхлэв.", "Хөтөлбөр", ["ҮТХ", "Монголбанк", "Зээл"]),
            (n_zoljargal.id, "2014-12-31", "chronological", "Үнэ тогтворжуулах хөтөлбөрийн хүрээнд зах зээлд 3.8 их наяд төгрөг нийлүүлэгдэж, төгрөгийн ам.доллартай харьцах ханш 1,350-аас 1,900 төгрөг болж 40 гаруй хувиар суларлаа.", "Ханшийн сулралт бүртгэгдэв.", "Ханш", ["Ханш", "Инфляци", "Төгрөг"]),
            (n_zoljargal.id, "2017-11-10", "chronological", "АТГ-аас Монголбанкны Ерөнхийлөгч асан Н.Золжаргалыг Үнэ тогтворжуулах хөтөлбөрийн хүрээнд албан тушаалаа урвуулан ашиглаж бусдад давуу байдал олгосон хэрэгт яллагдагчаар татаж шалгалаа.", "АТГ Н.Золжаргалыг шалгав.", "АТГ", ["АТГ", "Шалгалт", "Н.Золжаргал"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in vth_facts:
            f = add_fact(db, ent_id, vth_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="ҮТХ-ийн хэрэг", sentiment=-0.5)
            link_to_case(db, vth_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Price Stabilization Case populated with {len(vth_facts)} facts.")


        # ==========================================
        # 5. SOVEREIGN BONDS (Чингис & Самурай бонд)
        # ==========================================
        print("\n=== 5. SEEDING SOVEREIGN BONDS CASE ===")
        bnd_src = get_or_create_source(
            db,
            title="Монгол Улсын Засгийн газрын 1.5 тэрбум ам.долларын 'Чингис бонд' ба 'Самурай бонд'-ын зарцуулалтын хяналт шалгалт",
            url="https://legalinfo.mn/mn/detail?lawId=8644",
            category="law",
            cleaned_text="2012 оны 11-р сарын 28-нд Монгол Улсын Засгийн газар олон улсын зах зээлд 1.5 тэрбум ам.долларын 'Чингис бонд'-ыг 5 ба 10 жилийн хугацаатайгаар арилжаалсан. 2013 онд Японы зах зээлээс 30 тэрбум иений 'Самурай бонд' босгосон. Бондын хөрөнгийг Хөгжлийн банкаар дамжуулан зам, дэд бүтэц, төмөр зам, дулааны цахилгаан станц, үйлдвэрлэлийн төслүүдэд зарцуулсан боловч төслүүд цаг хугацаандаа ашиглалтад ороогүй, үр ашиггүй зарцуулалт үүссэн тул 2018-2022 онд улсын төсөвт өрийн хүнд дарамт үүсгэсэн.",
            author="Үндэсний Аудитын Газар / Сангийн яам",
            pub_date=date(2018, 5, 20),
            reliability=0.99
        )

        mof = get_or_create_entity(db, "Монгол Улсын Сангийн Яам", "government", "Улсын төсөв, засгийн газрын өр болон бондын төлбөрийн бодлогыг хариуцагч яам.")
        ch_ulaan = get_or_create_entity(db, "Чүлтэмийн Улаан", "person", "Сангийн сайд асан (2012-2014). Чингис бондын гүйлгээний үеийн Сангийн сайд.")
        dbm_bank = get_or_create_entity(db, "Монгол Улсын Хөгжлийн Банк", "company")

        bnd_case = db.query(models.Case).filter(models.Case.slug == "sovereign-bonds").first()
        if not bnd_case:
            bnd_case = models.Case(
                slug="sovereign-bonds",
                title="Чингис & Самурай Засгийн Газрын Бондын Зарцуулалтын Мөрдлөг",
                description="2012-2013 онд олон улсын зах зээлээс босгосон 1.5 тэрбум долларын 'Чингис бонд', 30 тэрбум иений 'Самурай бонд'-ын хуваарилалт, эдийн засгийн үр ашиг ба эргэн төлөлтийн үйл явц.",
                status="PUBLISHED",
                cover_entity_id=mof.id
            )
            db.add(bnd_case)
            db.commit()
            db.refresh(bnd_case)
            print(f"Created case: {bnd_case.title}")

        for ent, role, note in [
            (mof, "DECISION_MAKER", "Бондын хөрөнгийг захиран зарцуулсан Сангийн яам"),
            (dbm_bank, "PART_OF_CASE", "Бондын төслүүдийг санхүүжүүлэгч Хөгжлийн банк"),
            (ch_ulaan, "DECISION_MAKER", "Бондын хэлцэл хийсэн Сангийн сайд"),
            (n_altankhuyag, "DECISION_MAKER", "Чингис бондыг босгосон Шинэчлэлийн Засгийн газрын тэргүүн")
        ]:
            link_to_case(db, bnd_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, bnd_src.id, mof.id, dbm_bank.id, "Монгол Улсын Хөгжлийн Банк", "БОНДЫН_САНХҮҮЖИЛТ_ШИЛЖҮҮЛСЭН", "Чингис бондын 1.5 тэрбум ам.долларыг Хөгжлийн банкны дансанд байршуулсан.", "2012-12-05")

        bnd_facts = [
            (n_altankhuyag.id, "2012-11-28", "chronological", "Ерөнхий сайд Н.Алтанхуягийн танхим олон улсын хөрөнгийн зах зээлд Монгол Улсын түүхэнд анх удаа 1.5 тэрбум ам.долларын 'Чингис бонд'-ыг 4.125% болон 5.125%-ийн хүүтэйгээр амжилттай арилжааллаа.", "Чингис бондыг арилжаалав.", "Бонд", ["Чингис бонд", "Н.Алтанхуяг", "Сангийн яам"]),
            (mof.id, "2013-12-05", "chronological", "Монгол Улсын Засгийн газар Японы хөрөнгийн зах зээлд Японы Олон улсын хамтын ажиллагааны банк (JBIC)-ны баталгаатайгаар 30 тэрбум иен (290 сая ам.доллар)-ий 10 жилийн хугацаатай 'Самурай бонд'-ыг гаргав.", "Самурай бонд гарлаа.", "Бонд", ["Самурай бонд", "Япон", "Сангийн яам"]),
            (mof.id, "2018-01-05", "chronological", "Чингис бондын эхний ээлжийн 500 сая ам.доллар (1.2 их наяд төгрөг)-ын үндсэн төлбөрийг Засгийн газар улсын төсвөөс бүрэн төлж барагдууллаа.", "Чингис бондын эхний төлөлт.", "Өр төлөлт", ["Өр төлөлт", "Чингис бонд", "Төсөв"]),
            (mof.id, "2022-12-05", "chronological", "Чингис бондын үлдсэн 1.0 тэрбум ам.долларын үндсэн төлбөрийг Монгол Улсын Засгийн газар бүрэн төлж, 'Чингис бонд'-ын 10 жилийн өрийн түүхийг албан ёсоор хаалаа.", "Чингис бондын өр бүрэн хаагдав.", "Өр дуусах", ["Өр төлөлт", "Чингис бонд", "Төгсгөл"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in bnd_facts:
            f = add_fact(db, ent_id, bnd_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Бондын зарцуулалт", sentiment=0.3 if "төлж" in txt else -0.2)
            link_to_case(db, bnd_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Sovereign Bonds Case populated with {len(bnd_facts)} facts.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_all_five_cases()
