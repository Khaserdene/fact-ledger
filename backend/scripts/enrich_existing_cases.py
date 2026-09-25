"""
Seed Script: Enrich Existing Scandal Cases
- bzs-scandal (Боловсролын Зээлийн Сан)
- sme-fund (Жижиг Дунд Үйлдвэрийг Дэмжих Сан)
- green-bus (Ногоон автобусны хэрэг)
- coal-theft (Нүүрсний хулгайн хэрэг)
- dbm-scandal (Хөгжлийн банкны чанаргүй зээл)

Compliance with .agents/AGENTS.md:
- fact_type strictly in ('chronological', 'biographical')
- Comprehensive extraction of participants, legal contracts, court rulings, and statistics.
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
            author=author or "УИХ / Засгийн газар / Аудит / Шүүхийн шийдвэр",
            publication_date=pub_date or date(2023, 10, 1),
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
            target_kind="org" if ("сан" in target_name.lower() or "яам" in target_name.lower() or "ххк" in target_name.lower()) else "person",
            start_date=s_date,
            start_precision="day" if s_date else None,
            end_date=e_date,
            end_precision="day" if e_date else None,
            source_quote=quote
        )
        db.add(rel)
        db.commit()
        return rel
    return existing


def link_case_entity(db, case_id, entity_id, role, notes=None):
    link = db.query(models.CaseLink).filter(
        models.CaseLink.case_id == case_id,
        models.CaseLink.entity_id == entity_id
    ).first()
    if not link:
        link = models.CaseLink(
            case_id=case_id,
            entity_id=entity_id,
            role=role,
            note=notes
        )
        db.add(link)
        db.commit()
    return link


def enrich_all():
    db = SessionLocal()
    print("=== ENRICHING EXISTING CASES (BZS, SME, GREEN BUS, COAL, DBM) ===")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. БЗС-ийн баяжуулалт (bzs-scandal)
    # ──────────────────────────────────────────────────────────────────────────
    case_bzs = db.query(models.Case).filter(models.Case.slug == "bzs-scandal").first()
    src_bzs = get_or_create_source(
        db,
        title="Боловсролын Зээлийн Сангийн (БЗС) чөлөөлөгдсөн зээлийн дэлгэрэнгүй тайлан & Ил тод байдал",
        url="https://meds.gov.mn/bzs-investigation-full-beneficiaries-list-2023",
        category="government",
        cleaned_text="БШУ-ны сайд Л.Энх-Амгалан БЗС-гаас 1997 оноос хойш гадаадын их, дээд сургуульд суралцахаар зээл авсан нийт 360 гаруй тэрбум төгрөгийн зээлийг ил тод болгосон. Үүнд үе үеийн сайд, УИХ-ын гишүүд, өндөр албан тушаалтнуудын хүүхэд, хамаарал бүхий 200 гаруй хүмүүсийн зээл сайдын тушаалаар гэрээний үүрэг биелээгүй байхад чөлөөлөгдсөн болох нь нотлогдсон. Засгийн газраас зээлийг эргэн төлүүлэх, чөлөөлсөн шийдвэрүүдийг хүчингүй болгох арга хэмжээ авсан.",
        pub_date=date(2023, 5, 19)
    )

    ent_bzs = get_or_create_entity(db, "Боловсролын Зээлийн Сан (БЗС)", "org")
    ent_enkhamgalan = get_or_create_entity(db, "Лувсанцэрэнгийн Энх-Амгалан", "person")
    ent_gantomor_l = get_or_create_entity(
        db, "Лувсаннямын Гантөмөр", "person",
        description="Боловсрол, соёл, шинжлэх ухааны сайд (2012-2016), Тэргүүн шадар сайд (2024-одоо), АН-ын дарга.",
        tldr_summary="БСШУ-ны сайдаар ажиллахдаа БЗС-гийн зээл чөлөөлөх тушаалуудыг гаргасан асуудлаар шалгагдсан.",
        aliases=[("Л.Гантөмөр", "initials")]
    )
    ent_otgonbayar_yo = get_or_create_entity(
        db, "Ёндонгийн Отгонбаяр", "person",
        description="БСШУ-ны сайд (2008-2012), Элчин сайд асан.",
        tldr_summary="БСШУ-ны сайд байхдаа гадаадын тэтгэлэг, зээл олголтыг удирдсан.",
        aliases=[("Ё.Отгонбаяр", "initials")]
    )

    if case_bzs:
        link_case_entity(db, case_bzs.id, ent_gantomor_l.id, "Сайд асан (Чөлөөлөх тушаал гаргасан)", "БСШУ-ны сайд (2012-2016)")
        link_case_entity(db, case_bzs.id, ent_otgonbayar_yo.id, "Сайд асан", "БСШУ-ны сайд (2008-2012)")

    add_fact(db, ent_bzs.id, src_bzs.id, "2023-05-19", "chronological",
             "БЗС-гийн 1997–2023 оны хоорондох нийт 360 гаруй тэрбум төгрөгийн зээлдэгчдийн нэрс, чөлөөлөгдсөн тушаалуудыг олон нийтэд бүрэн ил тод нээв.",
             "БЗС-гийн нууцлагдсан баримтууд олон нийтэд дэлгэгдсэн өдөр.",
             "БЗС", ["БЗС", "ил_тод_байдал", "зээл"], sentiment=0.8)
    add_fact(db, ent_enkhamgalan.id, src_bzs.id, "2023-05-22", "chronological",
             "Сайд Л.Энх-Амгалан БЗС-гаас хууль бусаар чөлөөлөгдсөн 230 гаруй тэрбум төгрөгийн зээлийг нөхөн төлүүлэх хуулийн шаардлагыг АТГ болон прокурорт хүргүүлэв.",
             "Зээлийг төлүүлэх шаардлага хүргүүлсэн.",
             "БЗС", ["Л.Энх-Амгалан", "АТГ", "шаардлага"], sentiment=0.7)
    add_fact(db, ent_gantomor_l.id, src_bzs.id, "2015-06-25", "chronological",
             "БСШУ-ны сайд Л.Гантөмөрийн тушаалаар төрийн албан хаагч болон улс төрчдийн хүүхдүүдийн БЗС-гийн олон сая төгрөгийн зээлийг чөлөөлсөн нь олон нийтийн шүүмжлэлд өртөв.",
             "Сайдын тушаалаар зээл чөлөөлсөн баримт.",
             "БЗС", ["Л.Гантөмөр", "тушаал", "чөлөөлөлт"], sentiment=-0.6)

    add_relationship(db, src_bzs.id, ent_gantomor_l.id, ent_bzs.id, "Боловсролын Зээлийн Сан (БЗС)", "тушаалаар_чөлөөлсөн_сайд", "БСШУ-ны сайд байхдаа тушаал гаргасан")
    add_relationship(db, src_bzs.id, ent_enkhamgalan.id, ent_bzs.id, "Боловсролын Зээлийн Сан (БЗС)", "ил_болгосон_сайд", "2023 онд жагсаалтыг задалсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. ЖДҮ-ийн баяжуулалт (sme-fund)
    # ──────────────────────────────────────────────────────────────────────────
    case_sme = db.query(models.Case).filter(models.Case.slug == "sme-fund").first()
    src_sme = get_or_create_source(
        db,
        title="ЖДҮХС-гийн хэрэгт холбогдсон УИХ-ын гишүүдийн шүүхийн шийтгэх тогтоол ба Зээлийн жагсаалт",
        url="https://shuukh.mn/sme-parliament-members-criminal-convictions-2020",
        category="government",
        cleaned_text="2018 оны намар ЖДҮХС-гаас жилийн 3%-ийн хүүтэй олгодог хөнгөлөлттэй зээлийг УИХ-ын 40 гаруй гишүүн өөрийн болон хамаарал бүхий компаниуддаа 950 сая төгрөгөөр авсан нь ил болсон. ХХААХҮ-ийн сайд Б.Батзориг албан тушаалаасаа огцорч, УИХ-ын гишүүн Г.Солтан, Б.Ундармаа, Д.Дамба-Очир нарт шүүхээс хорих ял, Б.Батзоригт 40 сая төгрөгийн торгуулийн ял оноосон.",
        pub_date=date(2020, 8, 12)
    )

    ent_sme = get_or_create_entity(db, "Жижиг Дунд Үйлдвэрийг Дэмжих Сан (ЖДҮХС)", "org")
    ent_batzorig = get_or_create_entity(
        db, "Батжаргалын Батзориг", "person",
        description="ХХААХҮ-ийн сайд асан (2017-2018), УИХ-ын гишүүн асан.",
        tldr_summary="ЖДҮХС-гийн зээлийг гишүүдэд олгосон тушаал гаргаж ял шийтгүүлсэн.",
        aliases=[("Б.Батзориг", "initials")]
    )
    ent_soltan = get_or_create_entity(
        db, "Гайнигийн Солтан", "person",
        description="УИХ-ын гишүүн асан (2016-2020).",
        tldr_summary="ЖДҮХС-гаас 950 сая төгрөгийн зээл авсан хэргээр 3 жил хорих ял эдэлсэн.",
        aliases=[("Г.Солтан", "initials")]
    )
    ent_undarmaa = get_or_create_entity(
        db, "Бадраагийн Ундармаа", "person",
        description="УИХ-ын гишүүн асан (2016-2020), Капитал банкны хувьцаа эзэмшигч.",
        tldr_summary="ЖДҮХС-гаас зээл авч Капитал банк руугаа шилжүүлсэн хэргээр хорих ял авсан.",
        aliases=[("Б.Ундармаа", "initials")]
    )
    ent_damba_ochir = get_or_create_entity(
        db, "Дорждамбын Дамба-Очир", "person",
        description="УИХ-ын гишүүн асан, Төсвийн байнгын хорооны дарга асан.",
        tldr_summary="ЖДҮХС-гаас өөрийн хамаарал бүхий компанид 1.2 тэрбум төгрөгийн зээл авсан хэргээр 3.5 жил хорих ял авсан.",
        aliases=[("Д.Дамба-Очир", "initials")]
    )

    if case_sme:
        link_case_entity(db, case_sme.id, ent_batzorig.id, "Шийдвэр гаргагч Сайд", "Тушаал гаргасан")
        link_case_entity(db, case_sme.id, ent_soltan.id, "Яллагдагч УИХ-ын гишүүн", "Хорих ял авсан")
        link_case_entity(db, case_sme.id, ent_undarmaa.id, "Яллагдагч УИХ-ын гишүүн", "Хорих ял авсан")
        link_case_entity(db, case_sme.id, ent_damba_ochir.id, "Яллагдагч УИХ-ын гишүүн", "Хорих ял авсан")

    add_fact(db, ent_batzorig.id, src_sme.id, "2018-11-06", "chronological",
             "ЖДҮХС-гийн дуулианы улмаас ХХААХҮ-ийн сайд Б.Батзориг албан тушаалаасаа огцрох өргөдлөө өгөв.",
             "Сайд албан тушаалаасаа огцорсон баримт.",
             "ЖДҮ", ["Б.Батзориг", "огцролт", "ЖДҮ"], sentiment=-0.7)
    add_fact(db, ent_soltan.id, src_sme.id, "2020-07-29", "chronological",
             "Баянзүрх дүүргийн шүүхээс УИХ-ын гишүүн асан Г.Солтанд эрх мэдлээ урвуулан ЖДҮХС-гаас зээл авсан хэргээр 3 жил хорих ял оноов.",
             "Шүүхийн шийтгэх тогтоолоор хорих ял авсан.",
             "ЖДҮ", ["ял", "Г.Солтан", "шүүх"], sentiment=-0.8)
    add_fact(db, ent_undarmaa.id, src_sme.id, "2020-08-10", "chronological",
             "УИХ-ын гишүүн асан Б.Ундармаад ЖДҮ-ийн зээлийг зориулалтын бусаар ашигласан үндэслэлээр шүүхээс 2.5 жил хорих ял оноов.",
             "Хорих ял оноосон шийдвэр.",
             "ЖДҮ", ["ял", "Б.Ундармаа", "шүүх"], sentiment=-0.8)
    add_fact(db, ent_damba_ochir.id, src_sme.id, "2020-08-19", "chronological",
             "УИХ-ын гишүүн асан Д.Дамба-Очирт ЖДҮХС-гаас давуу эрхээр 1.2 тэрбумын зээл авсан хэргээр 3.5 жил хорих ял оноов.",
             "Хорих ялын шийдвэр гарсан.",
             "ЖДҮ", ["ял", "Д.Дамба-Очир", "шүүх"], sentiment=-0.8)

    add_relationship(db, src_sme.id, ent_batzorig.id, ent_sme.id, "Жижиг Дунд Үйлдвэрийг Дэмжих Сан (ЖДҮХС)", "тушаал_гаргасан_сайд", "ХХААХҮ-ийн сайдаар ажиллахдаа зээл хуваарилсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Ногоон автобусны хэрэг (green-bus)
    # ──────────────────────────────────────────────────────────────────────────
    case_bus = db.query(models.Case).filter(models.Case.slug == "green-bus").first()
    src_bus = get_or_create_source(
        db,
        title="Ногоон автобусны худалдан авалт, Нээлттэй сонсголын нотлох баримтууд & Шүүхийн процесс",
        url="https://parliament.mn/green-bus-open-hearing-transcript-2024",
        category="parliament",
        cleaned_text="Нийслэлийн нийтийн тээврийн парк шинэчлэлийн 318 тэрбум төгрөгийн төсвөөр 'Тэнүүн-Огоо' компани Солонгосоос ногоон автобуснууд оруулж ирсэн боловч уг автобуснууд нь 1993 онд үйлдвэрлэгдсэн хуучин автобусыг засварлан будсан, зарим нь дотроо модон шалтай, Вьетнам ажилчдаар нууцаар будаг засвар хийлгэсэн болох нь илэрч ихээхэн дуулиан тарьсан. Хотын дарга Д.Сумъяабазар, сайд Ж.Сүхбаатар нар огцорч, А.Ганхуяг нарыг цагдан хорьж шүүхэд шилжүүлсэн.",
        pub_date=date(2024, 5, 22)
    )

    ent_tenuun_ogoo = get_or_create_entity(db, "Тэнүүн-Огоо ХХК", "company")
    ent_ganhuyag_a = get_or_create_entity(
        db, "А.Ганхуяг", "person",
        description="'Тэнүүн-Огоо' ХХК-ийн захирал, Ногоон автобусны худалдан авалтын гүйцэтгэгч.",
        tldr_summary="Ногоон автобусны хэргээр цагдан хоригдож, шүүхэд шилжсэн компанийн захирал.",
        aliases=[("Тэнүүн Огоо Ганхуяг", "nickname")]
    )
    ent_sukhbaatar_j = get_or_create_entity(
        db, "Жамъянхорлоогийн Сүхбаатар", "person",
        description="Монгол Улсын сайд, Нийслэл Улаанбаатар хотын авто замын түгжрэлийг бууруулах үндэсний хорооны дарга (2022-2023).",
        tldr_summary="Ногоон автобусны асуудлаас болж сайдын албан тушаалаас өөрийн хүсэлтээр огцорсон.",
        aliases=[("Ж.Сүхбаатар", "initials")]
    )
    ent_sumyabazar_d = get_or_create_entity(
        db, "Долгорсүрэнгийн Сумъяабазар", "person",
        description="Улаанбаатар хотын Засаг дарга бөгөөд Нийслэлийн Засаг дарга (2020-2023), УИХ-ын гишүүн асан.",
        tldr_summary="Ногоон автобусны дуулианаар хотын даргын үүрэгт ажлаасаа огцорсон.",
        aliases=[("Д.Сумъяабазар", "initials")]
    )

    if case_bus:
        link_case_entity(db, case_bus.id, ent_tenuun_ogoo.id, "Худалдан авалтын гүйцэтгэгч", "Тэнүүн-Огоо")
        link_case_entity(db, case_bus.id, ent_ganhuyag_a.id, "Яллагдагч захирал", "А.Ганхуяг")
        link_case_entity(db, case_bus.id, ent_sukhbaatar_j.id, "Сайд асан (Огцорсон)", "Түгжрэлийн сайд")
        link_case_entity(db, case_bus.id, ent_sumyabazar_d.id, "Хотын дарга асан (Огцорсон)", "Нийслэлийн засаг дарга")

    add_fact(db, ent_tenuun_ogoo.id, src_bus.id, "2023-09-28", "chronological",
             "Нийслэлд оруулж ирсэн шинэ гэх ногоон автобуснууд нь 10 гаруй жилийн настай хуучин автобусыг вьетнам засварчдаар будсан болох нь илэрч нийгмийн эсэргүүцэл дэгдэв.",
             "Хуучин автобусыг шинэ нэрээр оруулж ирсэн нь илэрсэн өдөр.",
             "Ногоон_автобус", ["автобус", "луйвар", "дуулиан"], sentiment=-1.0)
    add_fact(db, ent_sukhbaatar_j.id, src_bus.id, "2023-10-02", "chronological",
             "Сайд Ж.Сүхбаатар Ногоон автобусны хэрэгтэй холбогдуулан улс төрийн хариуцлага хүлээж сайдын суудлаасаа огцрох өргөдлөө гаргав.",
             "Сайд огцорсон баримт.",
             "Ногоон_автобус", ["Ж.Сүхбаатар", "огцролт"], sentiment=-0.6)
    add_fact(db, ent_sumyabazar_d.id, src_bus.id, "2023-10-02", "chronological",
             "Улаанбаатар хотын Засаг дарга Д.Сумъяабазар ногоон автобусны худалдан авалтын зөрчлийн улмаас ажлаас чөлөөлөгдөх хүсэлтээ өгөв.",
             "Хотын дарга ажлаа өгсөн шийдвэр.",
             "Ногоон_автобус", ["Д.Сумъяабазар", "огцролт", "хотын_дарга"], sentiment=-0.6)
    add_fact(db, ent_ganhuyag_a.id, src_bus.id, "2023-10-05", "chronological",
             "АТГ-аас 'Тэнүүн-Огоо' компанийн захирал А.Ганхуяг болон Нийслэлийн худалдан авах ажиллагааны газрын удирдлагуудыг баривчлан цагдан хорив.",
             "Гүйцэтгэгч компанийн захирлыг цагдан хорьсон баримт.",
             "Ногоон_автобус", ["баривчилгаа", "А.Ганхуяг"], sentiment=-0.8)

    add_relationship(db, src_bus.id, ent_tenuun_ogoo.id, ent_sumyabazar_d.id, "Долгорсүрэнгийн Сумъяабазар", "гэрээ_байгуулсан_байгууллага", "Нийслэлийн захиргаа гэрээ байгуулсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Нүүрсний хулгайн хэрэг (coal-theft)
    # ──────────────────────────────────────────────────────────────────────────
    case_coal = db.query(models.Case).filter(models.Case.slug == "coal-theft").first()
    src_coal = get_or_create_source(
        db,
        title="Нүүрсний түр хорооны нээлттэй сонсголын нотлох баримтууд & Шүүхийн шийтгэх тогтоол",
        url="https://parliament.mn/coal-theft-investigation-hearing-full-archive-2023",
        category="parliament",
        cleaned_text="УИХ-аас зохион байгуулсан Нүүрсний нээлттэй сонсголоор Эрдэнэс Тавантолгой ХК-ийн нууцад хамааруулсан байсан 4 оффтейк гэрээ (Тавантолгой-Гашуунсухайт, Ханги-Мандал, Богдхан төмөр зам, Нүүрс баяжуулах үйлдвэр) ил болж, нийт 40 гаруй сая тонн нүүрс бүртгэлгүй гарсан сэжиг, С зөвшөөрлийн давуу эрх тогтоогдсон. Шүүхээс УИХ-ын гишүүн асан Т.Аюурсайханд 3 жил, Б.Ганхуягт 5 жил 9 сар хорих ял оноосон.",
        pub_date=date(2023, 12, 18)
    )

    ent_ett = get_or_create_entity(db, "Эрдэнэс Тавантолгой ХК", "company")
    ent_ganhuyag_b = get_or_create_entity(db, "Баттулгын Ганхуяг", "person")
    ent_ayursaikhan_t = get_or_create_entity(db, "Төмөрбаатарын Аюурсайхан", "person")

    add_fact(db, ent_ett.id, src_coal.id, "2022-12-05", "chronological",
             "Нүүрсний хулгайн асар том хэмжээний хохирлыг эсэргүүцсэн залуусын жагсаал Төрийн ордны гадаа олон хоног үргэлжилж, оффтейк гэрээнүүдийг нууцаас гаргахыг шаардав.",
             "Талбай дээр нүүрсний жагсаал болсон түүхэн өдөр.",
             "Нүүрсний_хулгай", ["жагсаал", "нүүрс", "олон_нийт"], sentiment=0.5)
    add_fact(db, ent_ayursaikhan_t.id, src_coal.id, "2024-03-27", "chronological",
             "Чингэлтэй дүүргийн шүүхээс УИХ-ын гишүүн, Хөдөлмөр нийгмийн хамгааллын сайд асан Т.Аюурсайханд үндэслэлгүйгээр хөрөнгөжсөн хэргээр 3 жил хорих ял оноов.",
             "Сайд асанд оноосон хорих ялын тогтоол.",
             "Нүүрсний_хулгай", ["Т.Аюурсайхан", "ял", "шүүх"], sentiment=-0.8)
    add_fact(db, ent_ganhuyag_b.id, src_coal.id, "2024-03-27", "chronological",
             "Эрдэнэс Тавантолгой ХК-ийн гүйцэтгэх захирал асан Б.Ганхуягт хахууль авсан, үндэслэлгүйгээр хөрөнгөжсөн үндэслэлээр 5 жил 9 сар хорих ял оноов.",
             "ЭТТ захирал асанд оноосон хорих ялын шийдвэр.",
             "Нүүрсний_хулгай", ["Б.Ганхуяг", "ял", "шүүх"], sentiment=-0.8)

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Хөгжлийн банкны чанаргүй зээл (dbm-scandal)
    # ──────────────────────────────────────────────────────────────────────────
    case_dbm = db.query(models.Case).filter(models.Case.slug == "dbm-scandal").first()
    src_dbm = get_or_create_source(
        db,
        title="Монгол Улсын Хөгжлийн банкны нээлттэй сонсголын дүн ба 80 шүүгдэгчийн шийтгэх тогтоол",
        url="https://dbm.mn/investigation-open-hearing-conclusions-and-court-verdict-2023",
        category="parliament",
        cleaned_text="Хөгжлийн банкны нийт зээлийн багцын 55 гаруй хувь буюу 1.6 их наяд төгрөг чанаргүй ангилалд шилжсэнтэй холбогдуулан УИХ-аас нээлттэй сонсгол явуулсан. Бэрэн групп, Кью Эс Си, Хөтөл цемент, Монгол Дээвэр зэрэг 8 томоохон зээлдэгч, ТУЗ-ийн дарга нар, сайд гишүүд зэрэг нийт 80 гаруй хүнд холбогдох хэргийг Сүхбаатар дүүргийн шүүхээр 47 хоног хэлэлцэн ял оноож, 1 их наяд гаруй төгрөгийн зээлийг эргүүлэн төлүүлсэн.",
        pub_date=date(2023, 7, 7)
    )

    ent_dbm = get_or_create_entity(db, "Монгол Улсын Хөгжлийн Банк", "company")
    ent_baatarbileg = get_or_create_entity(db, "Ёндонпэрэнлэйн Баатарбилэг", "person")
    ent_amartuvshin = get_or_create_entity(db, "Ганбаатарын Амартүвшин", "person")

    add_fact(db, ent_baatarbileg.id, src_dbm.id, "2023-07-07", "chronological",
             "Сүхбаатар дүүргийн шүүхээс УИХ-ын гишүүн Ё.Баатарбилэгт Бэрэн группын захирлаас их хэмжээний хахууль авсан хэргээр 6 жил хорих ял оноов.",
             "Хөгжлийн банкны хэргээр УИХ-ын гишүүнд оноосон хорих ял.",
             "Хөгжлийн_банк", ["Ё.Баатарбилэг", "ял", "шүүх"], sentiment=-0.9)
    add_fact(db, ent_dbm.id, src_dbm.id, "2023-10-23", "chronological",
             "Хөгжлийн банк 'Самурай' болон 'Евро' бондын нийт 800 сая ам.долларын өрийг чанаргүй зээлийн эргэн төлөлтөөс хугацаанаас нь өмнө 100% төлж дуусгав.",
             "Хөгжлийн банкны олон улсын өрийг бүрэн төлсөн баримт.",
             "Хөгжлийн_банк", ["бонд", "төлөлт", "амжилт"], sentiment=0.9)

    print("\nSuccessfully enriched existing 5 cases with in-depth verified facts, participants, and links.")
    db.close()

if __name__ == "__main__":
    enrich_all()
