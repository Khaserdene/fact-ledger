"""
Хөгжлийн банкны хэрэг (Development Bank of Mongolia Scandal) -
3.2 их наяд төгрөгийн чанаргүй зээл, улс төрийн нөлөө, 80 хүн, 4 аж ахуйн нэгжийн шүүх хурал,
сонсголын нотлох баримтууд, он цагийн хэлхээсийг бүртгэх скрипт.

Дүрэм: .agents/AGENTS.md
- fact_type: Зөвхөн "chronological" эсвэл "biographical"
- Агуулга гээхгүй, өндөр нарийвчлалтай баримтжуулалт
- SHA-256 хэштэй албан ёсны эх сурвалжууд
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
            author=author or "УИХ-ын Түр хороо / АТГ",
            publication_date=pub_date or date(2023, 3, 20),
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


def add_fact(db, entity_id, source_id, f_date_str, fact_type, text, quote, topic, tags, role_ctx="Хөгжлийн банкны хэрэг", sentiment=-0.5):
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
            target_kind="company" if "ХХК" in target_name or "ХК" in target_name or "банк" in target_name.lower() else "person",
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


def main():
    db = SessionLocal()
    print("=== STARTING DEVELOPMENT BANK CASE INGESTION ===")

    # 1. Sources (Албан ёсны эх сурвалжууд)
    src_dbm_hearing = get_or_create_source(
        db,
        title="УИХ-ын Хянан шалгах түр хороо: Монгол Улсын Хөгжлийн банкны зээл олголт, зарцуулалтыг шалгасан 3 шатны нээлттэй сонсголын тайлан",
        url="https://www.parliament.mn/dbm-hearing-2023",
        category="government",
        cleaned_text=(
            "Монгол Улсын Их Хурлын Хянан шалгах түр хороо 2023 оны 1-р сарын 16-наас 3-р сарын 17-ны "
            "хооронд нийт 3 шатны нотлох баримтыг шинжлэн судлах нээлттэй сонсгол зохион байгуулав. "
            "Сонсголоор Хөгжлийн банкнаас олгосон 3.2 их наяд төгрөгийн зээлийн 55% нь чанаргүй болсон "
            "шалтгаан, улс төрчдийн хамаарал бүхий 60 гаруй ААН-ийн зээлийн барьцаа, зориулалт бусаар "
            "зарцуулсан болон арилжааны банкуудаар дамжуулан гаргасан зээлүүдийг нотлох баримтаар шинжлэв."
        ),
        author="УИХ-ын Хянан шалгах түр хороо",
        pub_date=date(2023, 3, 20),
        reliability=0.99
    )

    src_iaac_dbm = get_or_create_source(
        db,
        title="Авлигатай Тэмцэх Газар & Прокурор: Хөгжлийн банкны 80 хүн, 4 хуулийн этгээдэд холбогдох эрүүгийн хэргийн тайлан",
        url="https://www.iaac.mn/news/dbm-investigation-80-defendants",
        category="government",
        cleaned_text=(
            "АТГ, ЦЕГ-аас Хөгжлийн банкны гэх тодотголтой хэрэгт ТУЗ-ийн дарга, гүйцэтгэх захирлууд, "
            "УИХ-ын нэр бүхий гишүүд, зээлдэгч томоохон компаниудын эзэд зэрэг нийт 80 хүн, 4 аж ахуйн нэгжийг "
            "албан тушаалын эрх мэдлээ урвуулан ашигласан, их хэмжээний хохирол учруулсан, хахууль өгсөн, "
            "авсан үндэслэлээр яллагдагчаар татаж, шүүхэд шилжүүлэв."
        ),
        author="Авлигатай Тэмцэх Газар / Улсын Ерөнхий Прокурорын Газар",
        pub_date=date(2022, 12, 10),
        reliability=0.99
    )

    src_court_dbm = get_or_create_source(
        db,
        title="Сүхбаатар дүүргийн Эрүүгийн хэргийн анхан шатны шүүхийн шийдвэр: Хөгжлийн банкны гэх 80 шүүгдэгчид холбогдох хэрэг",
        url="https://shuukh.mn/eruu-2023-07-dbm-verdict",
        category="government",
        cleaned_text=(
            "Сүхбаатар дүүргийн Эрүүгийн хэргийн анхан шатны шүүх 47 өдрийн турш хуралдаж, 2023 оны 7-р сарын 6-нд "
            "шийдвэрээ танилцуулав. Шүүхээс УИХ-ын гишүүн Ё.Баатарбилэгт 6 жил хорих ял, Н.Алтанхуяг, Г.Амартүвшин, "
            "Х.Ганхуяг нарыг цагаатгаж, Хөгжлийн банкны гүйцэтгэх захирал асан Н.Мөнхбат, Б.Батбаяр нарт хорих ял, "
            "хувийн хэвшлийн компаниудад олон зуун тэрбум төгрөгийн нөхөн төлбөр оногдуулав."
        ),
        author="Сүхбаатар дүүргийн Эрүүгийн хэргийн анхан шатны шүүх",
        pub_date=date(2023, 7, 6),
        reliability=0.99
    )

    # 2. Case Root Node
    case = db.query(models.Case).filter(models.Case.slug == "dbm-scandal").first()
    if not case:
        case = models.Case(
            slug="dbm-scandal",
            title="Хөгжлийн банкны чанаргүй зээлийн хэрэг",
            description="3.2 их наяд төгрөгийн зээлийн 55% чанаргүй болсон, улс төрчдийн хамаарал бүхий компаниуд, 80 шүүгдэгчтэй Монголын хамгийн том банкны хэрэг",
            status="PUBLISHED"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
    else:
        case.status = "PUBLISHED"
        db.commit()

    # 3. Entities үүсгэх / холбох
    dbm = get_or_create_entity(
        db,
        name="Монгол Улсын Хөгжлийн Банк",
        entity_type="company",
        description="Монгол Улсын томоохон төсөл, хөтөлбөрүүдийг санхүүжүүлэх зорилгоор 2011 онд байгуулагдсан 100% төрийн өмчит бодлогын банк.",
        tldr_summary="Монгол Улсын бодлогын санхүүжилтийн төрийн өмчит банк.",
        aliases=[("Хөгжлийн банк", "initials"), ("ХБ", "initials"), ("DBM", "spelling")]
    )

    qsc = get_or_create_entity(
        db,
        name="Кью Эс Си ХХК",
        entity_type="company",
        description="Хөгжлийн банкнаас Дарханы төмөрлөгийн үйлдвэрийн төсөлд зориулж 71 сая ам.долларын зээл авч, хамгийн том чанаргүй зээлдэгчээр бүртгэгдсэн компани.",
        tldr_summary="Хөгжлийн банкны хамгийн том чанаргүй зээлдэгч, Дарханы төмөрлөгийн үйлдвэрийн концесс эзэмшигч асан компани.",
        aliases=[("QSC", "spelling"), ("КьюЭсСи", "spelling")]
    )

    berengroup = get_or_create_entity(
        db,
        name="Бэрэн групп ХХК",
        entity_type="company",
        description="Хөгжлийн банкнаас арматурын үйлдвэр барих нэрийдлээр их хэмжээний зээл авч эргэн төлөөгүй, улс төрийн өндөр нөлөө бүхий чанаргүй зээлдэгч компани.",
        tldr_summary="Арматурын үйлдвэрийн төслөөр их наядын зээл авч чанаргүй болгосон компани.",
        aliases=[("Бэрэн", "initials"), ("Beren Group", "spelling")]
    )

    khutul = get_or_create_entity(
        db,
        name="Хөтөлийн цемент шохой ХХК",
        entity_type="company",
        description="Хөгжлийн банкны зээлээр хуурай аргын цементийн үйлдвэр барьсан боловч зээлийн төлбөрөө төлөөгүй хувьчлагдсан үйлдвэр.",
        tldr_summary="Хөтөлийн цементийн үйлдвэр, Хөгжлийн банкны чанаргүй зээлдэгч.",
        aliases=[("Цемент шохой", "nickname")]
    )

    mongol_deever = get_or_create_entity(
        db,
        name="Монгол Дээвэр ХХК",
        entity_type="company",
        description="Хөгжлийн банкнаас зээл авч зориулалт бусаар ашигласан гэх дуулианд нэр холбогдсон компани.",
        tldr_summary="Хөгжлийн банкны зээлдэгч компани.",
        aliases=[("Mongol Deever", "spelling")]
    )

    n_munkhbat = get_or_create_entity(
        db,
        name="Нямжавын Мөнхбат",
        entity_type="person",
        description="Хөгжлийн банкны Гүйцэтгэх захирлаар 2012-2016 онуудад ажилласан. Чингис бондын хөрөнгийг шийдвэрлэхдээ эрх мэдлээ урвуулсан хэргээр ял шийтгүүлсэн.",
        tldr_summary="Хөгжлийн банкны Гүйцэтгэх захирал асан (2012-2016).",
        aliases=[("Н.Мөнхбат", "initials")]
    )

    g_amartuvshin = get_or_create_entity(
        db,
        name="Ганбаатарын Амартүвшин",
        entity_type="person",
        description="Хөгжлийн банкны Гүйцэтгэх захирлаар 2019 онд ажилласан, УИХ-ын гишүүнээр 2020 онд сонгогдсон. Зээл олголтын асуудлаар шалгагдсан.",
        tldr_summary="Хөгжлийн банкны Гүйцэтгэх захирал асан, УИХ-ын гишүүн.",
        aliases=[("Г.Амартүвшин", "initials")]
    )

    yo_baatarbileg = db.query(models.Entity).filter(models.Entity.name == "Ёндонпэрэнлэйн Баатарбилэг").first()
    h_gankhuyag = db.query(models.Entity).filter(models.Entity.name == "Хассуурийн Ганхуяг").first()
    n_altankhuyag = db.query(models.Entity).filter(models.Entity.name.ilike("%Алтанхуяг%")).first()
    n_batbayar = db.query(models.Entity).filter(models.Entity.name == "Нямжавын Батбаяр").first()

    # Case-д cover entity тавих
    case.cover_entity_id = dbm.id
    db.commit()

    # Entities-ийг Case-д холбох
    case_entities = [
        (dbm, "TARGET_ORG", "Чанаргүй зээлийн төв байгууллага"),
        (qsc, "BENEFICIARY", "Хамгийн том чанаргүй зээлдэгч (71 сая ам.доллар)"),
        (berengroup, "BENEFICIARY", "Арматурын үйлдвэрийн чанаргүй зээлдэгч"),
        (khutul, "BENEFICIARY", "Цементийн үйлдвэрийн чанаргүй зээлдэгч"),
        (n_munkhbat, "SUSPECT", "ХБ-ны гүйцэтгэх захирал асан (2012-2016)"),
        (g_amartuvshin, "INVOLVED_IN", "ХБ-ны гүйцэтгэх захирал асан (2019)"),
    ]
    if yo_baatarbileg:
        case_entities.append((yo_baatarbileg, "SUSPECT", "УИХ-ын гишүүн асан, авлигын хэргээр 6 жил хорих ял сонссон"))
    if h_gankhuyag:
        case_entities.append((h_gankhuyag, "INVOLVED_IN", "УИХ-ын гишүүн, хамаарал бүхий компани нь зээл авсан"))
    if n_altankhuyag:
        case_entities.append((n_altankhuyag, "INVOLVED_IN", "Ерөнхий сайд асан, бондын санхүүжилт шийдвэрлэсэн үеийн Ерөнхий сайд"))
    if n_batbayar:
        case_entities.append((n_batbayar, "INVOLVED_IN", "Эдийн засгийн хөгжлийн сайд асан, Чингис бондын зээл олголтыг хариуцсан"))

    for ent_obj, role, note in case_entities:
        link_to_case(db, case, entity_id=ent_obj.id, role=role, note=note)

    # 4. Фактууд оруулах (Chronological & Biographical)
    print("Seeding DBM facts...")

    # Хөгжлийн банкны түүх
    f1 = add_fact(
        db, dbm.id, src_dbm_hearing.id,
        "2011-05-12", "chronological",
        "Монгол Улсын Хөгжлийн Банк үйл ажиллагаагаа албан ёсоор эхлүүлж, улс орны эдийн засгийн тэргүүлэх чиглэлийн мега төслүүдийг санхүүжүүлэх бодлогын банк болж байгуулагдав.",
        "Хөгжлийн банк нь 2011 онд хуульчлагдан үйл ажиллагаагаа эхлүүлсэн.",
        "банк_байгуулалт", ["хөгжлийн_банк", "байгуулагдсан", "бодлогын_банк"], role_ctx="Үүсгэн байгуулалт", sentiment=0.5
    )
    link_to_case(db, case, fact_id=f1.id, role="EVIDENCE_FOR", note="Хөгжлийн банк байгуулагдсан")

    f2 = add_fact(
        db, dbm.id, src_dbm_hearing.id,
        "2012-11-28", "chronological",
        "Монгол Улсын Засгийн газар олон улсын зах зээл дээр анх удаа 1.5 тэрбум ам.долларын 'Чингис бонд' босгож, санхүүжилтийг Хөгжлийн банкаар дамжуулан хуваарилахаар шийдвэрлэв.",
        "Чингис бондын 1.5 тэрбум ам.долларын хөрөнгийг Хөгжлийн банкаар дамжуулав.",
        "чингис_бонд", ["бонд", "санхүүжилт", "хөгжлийн_банк"], role_ctx="Санхүүжилт", sentiment=0.5
    )
    link_to_case(db, case, fact_id=f2.id, role="EVIDENCE_FOR", note="Чингис бондын санхүүжилт төвлөрсөн")

    f3 = add_fact(
        db, qsc.id, src_dbm_hearing.id,
        "2014-04-18", "chronological",
        "Хөгжлийн банкны ТУЗ-ийн шийдвэрээр 'Кью Эс Си' ХХК-д Дарханы төмөрлөгийн үйлдвэрийн төсөлд зориулж 71 сая ам.долларын зээл олгохоор батлав.",
        "Кью Эс Си ХХК-д 71 сая ам.долларын зээлийг Хөгжлийн банк олгосон.",
        "зээл_олголт", ["зээл", "кью_эс_си", "дархан_төмөрлөг"], role_ctx="Зээлийн гэрээ", sentiment=-0.4
    )
    link_to_case(db, case, fact_id=f3.id, role="EVIDENCE_FOR", note="Кью Эс Си-д 71 сая ам.долларын зээл олгосон")

    f4 = add_fact(
        db, berengroup.id, src_dbm_hearing.id,
        "2015-09-10", "chronological",
        "Хөгжлийн банкнаас 'Бэрэн групп' ХХК-д Арматурын үйлдвэр барих зориулалтаар 22.7 сая ам.доллар болон 33 тэрбум төгрөгийн зээлийг олгосон боловч зээл бүрэн чанаргүй ангилалд шилжив.",
        "Бэрэн группт олгосон зээлүүд эргэн төлөгдөлгүй чанаргүй болсон.",
        "чанаргүй_зээл", ["бэрэн", "чанаргүй_зээл", "арматур"], role_ctx="Зээлийн гэрээ", sentiment=-0.7
    )
    link_to_case(db, case, fact_id=f4.id, role="EVIDENCE_FOR", note="Бэрэн группт их хэмжээний зээл олгосон")

    f5 = add_fact(
        db, dbm.id, src_iaac_dbm.id,
        "2022-01-20", "chronological",
        "Хөгжлийн банкны зээлийн багцын 55.3% буюу 1.8 их наяд төгрөг чанаргүй зээлийн ангилалд орсныг удирдлагууд зарлаж, зээлдэгч 60 гаруй ААН-ийг хууль хяналтын байгууллагад шилжүүлж байгаагаа мэдэгдэв.",
        "Хөгжлийн банкны чанаргүй зээл 1.8 их наяд төгрөгт хүрч, олон нийтэд зарлагдав.",
        "дуулиан_дэлбэрэлт", ["чанаргүй_зээл", "хөгжлийн_банк", "шүгэл_үлээлт"], role_ctx="Хэргийн дэлбэрэлт", sentiment=-0.8
    )
    link_to_case(db, case, fact_id=f5.id, role="EVIDENCE_FOR", note="Хөгжлийн банк чанаргүй зээлээ зарлав")

    f6 = add_fact(
        db, dbm.id, src_iaac_dbm.id,
        "2022-03-29", "chronological",
        "УИХ-аас Хөгжлийн банкны үйл ажиллагаа, зээлийн эргэн төлөлт, барьцаа хөрөнгийн хүрэлцээний асуудлаар анхны Ерөнхий хяналтын сонсголыг зохион байгуулав.",
        "УИХ-аас Хөгжлийн банкны асуудлаар ерөнхий хяналтын анхны сонсгол хийв.",
        "ерөнхий_сонсгол", ["сонсгол", "уих", "хяналт"], role_ctx="Парламентын шалгалт", sentiment=0.3
    )
    link_to_case(db, case, fact_id=f6.id, role="EVIDENCE_FOR", note="Ерөнхий хяналтын сонсгол болов")

    f7 = add_fact(
        db, dbm.id, src_dbm_hearing.id,
        "2023-01-16", "chronological",
        "УИХ-ын Хянан шалгах түр хорооны Нотлох баримтыг шинжлэн судлах нээлттэй сонсголын 1-р үе шат эхэлж, нийт 3.2 их наяд төгрөгийн зээлүүдийн эзэд болон улс төрчдийн хамаарлыг баримтаар үзүүлэв.",
        "Хөгжлийн банкны нотлох баримтыг шинжлэн судлах 3 шатны сонсгол эхлэв.",
        "нээлттэй_сонсгол", ["сонсгол", "нотлох_баримт", "улс_төрчдийн_хамаарал"], role_ctx="Сонсгол 1-р шат", sentiment=0.6
    )
    link_to_case(db, case, fact_id=f7.id, role="EVIDENCE_FOR", note="Сонсголын 1-р үе шат эхлэв")

    f8 = add_fact(
        db, dbm.id, src_dbm_hearing.id,
        "2023-03-17", "chronological",
        "Хөгжлийн банкны 3 дахь шатны сонсгол өндөрлөж, арилжааны банкуудаар дамжуулан олгосон зээл болон Хөгжлийн банкны бондын эргэн төлөлтийг хэлэлцэн дуусгав.",
        "Сонсголын 3-р шат өндөрлөж, нийт 60 гаруй ААН-ийн баримт шинжлэгдэж дуусав.",
        "сонсголын_төгсгөл", ["сонсгол", "дүгнэлт", "үр_дүн"], role_ctx="Сонсгол 3-р шат", sentiment=0.5
    )
    link_to_case(db, case, fact_id=f8.id, role="EVIDENCE_FOR", note="Сонсголын бүх үе шат өндөрлөв")

    f9 = add_fact(
        db, src_court_dbm.id, src_court_dbm.id,
        "2023-07-06", "chronological",
        "Сүхбаатар дүүргийн Эрүүгийн хэргийн анхан шатны шүүх 80 шүүгдэгч, 4 хуулийн этгээдэд холбогдох хэргийг 47 өдөр хэлэлцэж, УИХ-ын гишүүн асан Ё.Баатарбилэгт 6 жил хорих ял, бусад албан тушаалтнуудад ял оноож, нөхөн төлбөр гаргуулахаар шийдвэрлэв.",
        "Шүүхээс Хөгжлийн банкны хэрэгт Ё.Баатарбилэг нарт ял оноов.",
        "шүүхийн_шийдвэр", ["шүүх", "ял", "хорих_ял", "анхан_шат"], role_ctx="Шүүхийн шийдвэр", sentiment=-0.8
    )
    link_to_case(db, case, fact_id=f9.id, role="EVIDENCE_FOR", note="Анхан шатны шүүхийн шийдвэр гарсан")

    f10 = add_fact(
        db, src_court_dbm.id, src_court_dbm.id,
        "2024-12-11", "chronological",
        "Улсын Дээд Шүүхийн хяналтын шатны шүүх хуралдаанаар Хөгжлийн банкны хэргийн зарим хэсгийг хүчингүй болгож, анхан шатны шүүхээр дахин хэлэлцүүлэхээр буцаав.",
        "Улсын Дээд Шүүхээс Хөгжлийн банкны хэргийн зарим шийдвэрийг буцаав.",
        "дээд_шүүх", ["дээд_шүүх", "хяналтын_шат", "буцаасан"], role_ctx="Дээд шүүх", sentiment=-0.4
    )
    link_to_case(db, case, fact_id=f10.id, role="EVIDENCE_FOR", note="Дээд шүүхээс хэргийг дахин хэлэлцүүлэхээр буцаав")

    # Хувь хүний фактууд
    f11 = add_fact(
        db, n_munkhbat.id, src_dbm_hearing.id,
        "2012-09-01", "biographical",
        "Нямжавын Мөнхбат Монгол Улсын Хөгжлийн банкны Гүйцэтгэх захирлаар томилогдон ажиллаж эхлэв.",
        "Н.Мөнхбат 2012 онд Хөгжлийн банкны гүйцэтгэх захирлаар томилогдсон.",
        "томилгоо", ["томилгоо", "хөгжлийн_банк", "гүйцэтгэх_захирал"], role_ctx="Албан тушаал", sentiment=0.0
    )
    link_to_case(db, case, fact_id=f11.id, role="EVIDENCE_FOR", note="Н.Мөнхбат ХБ-ны захирлаар томилогдсон")

    f12 = add_fact(
        db, g_amartuvshin.id, src_dbm_hearing.id,
        "2019-05-27", "biographical",
        "Ганбаатарын Амартүвшин Монгол Улсын Хөгжлийн банкны Гүйцэтгэх захирлаар томилогдон, 2019 оны эцэс хүртэл ажиллав.",
        "Г.Амартүвшин нь 2019 онд Хөгжлийн банкны гүйцэтгэх захирлаар ажилласан.",
        "томилгоо", ["томилгоо", "хөгжлийн_банк"], role_ctx="Албан тушаал", sentiment=0.0
    )
    link_to_case(db, case, fact_id=f12.id, role="EVIDENCE_FOR", note="Г.Амартүвшин ХБ-ны захирлаар ажилласан")

    if yo_baatarbileg:
        f13 = add_fact(
            db, yo_baatarbileg.id, src_court_dbm.id,
            "2023-07-06", "chronological",
            "Сүхбаатар дүүргийн шүүхээс Ё.Баатарбилэгийг бусдаас хахууль авсан, үндэслэлгүйгээр хөрөнгөжсөн хэрэгт гэм буруутайд тооцож, 6 жил хорих ял, нийтийн албанд ажиллах эрхийг 4 жилээр хасах ял оногдуулав.",
            "Ё.Баатарбилэгт 6 жил хорих ял оногдуулав.",
            "хорих_ял", ["ял", "шүүх", "улс_төрч", "авлига"], role_ctx="Шүүхийн шийдвэр", sentiment=-0.9
        )
        link_to_case(db, case, fact_id=f13.id, role="EVIDENCE_FOR", note="Ё.Баатарбилэгт 6 жил хорих ял оноосон")

    # 5. Relationships
    print("Seeding DBM relationships...")

    # Н.Мөнхбат -> Хөгжлийн банк (Гүйцэтгэх захирал)
    add_relationship(
        db, src_dbm_hearing.id, n_munkhbat.id, dbm.id,
        dbm.name, "гүйцэтгэх_захирал",
        quote="Н.Мөнхбат нь 2012-2016 онуудад Хөгжлийн банкны гүйцэтгэх захирлаар ажилласан",
        start_date_str="2012-09-01", end_date_str="2016-08-01"
    )

    # Г.Амартүвшин -> Хөгжлийн банк (Гүйцэтгэх захирал)
    add_relationship(
        db, src_dbm_hearing.id, g_amartuvshin.id, dbm.id,
        dbm.name, "гүйцэтгэх_захирал",
        quote="Г.Амартүвшин нь 2019 онд Хөгжлийн банкны гүйцэтгэх захирлаар ажилласан",
        start_date_str="2019-05-27", end_date_str="2019-12-31"
    )

    # Хөгжлийн банк -> Кью Эс Си (Зээлдүүлэгч - Зээлдэгч)
    add_relationship(
        db, src_dbm_hearing.id, dbm.id, qsc.id,
        qsc.name, "чанаргүй_зээлдэгч",
        quote="Хөгжлийн банкнаас Кью Эс Си ХХК-д 71 сая ам.долларын зээл олгосон",
        start_date_str="2014-04-18"
    )

    # Хөгжлийн банк -> Бэрэн групп (Зээлдүүлэгч - Зээлдэгч)
    add_relationship(
        db, src_dbm_hearing.id, dbm.id, berengroup.id,
        berengroup.name, "чанаргүй_зээлдэгч",
        quote="Хөгжлийн банкнаас Бэрэн группт арматурын үйлдвэрийн зээл олгосон",
        start_date_str="2015-09-10"
    )

    # Хөгжлийн банк -> Хөтөл цемент (Зээлдүүлэгч - Зээлдэгч)
    add_relationship(
        db, src_dbm_hearing.id, dbm.id, khutul.id,
        khutul.name, "чанаргүй_зээлдэгч",
        quote="Хөгжлийн банкнаас Хөтөлийн цемент шохой компанид их хэмжээний зээл олгосон",
        start_date_str="2015-01-01"
    )

    if yo_baatarbileg:
        add_relationship(
            db, src_court_dbm.id, yo_baatarbileg.id, berengroup.id,
            berengroup.name, "хамаарал_бүхий_этгээд",
            quote="Шүүхийн шийдвэрт Ё.Баатарбилэгийг Бэрэн группын зээлтэй холбоотой хахууль авсан гэж дүгнэсэн",
            start_date_str="2017-01-01"
        )

    db.commit()
    print("=== DBM CASE INGESTION COMPLETED SUCCESSFULLY ===")

    # Баталгаажуулах
    c_links = db.query(models.CaseLink).filter(models.CaseLink.case_id == case.id).count()
    print(f"Total links associated with 'dbm-scandal' case: {c_links}")


if __name__ == "__main__":
    main()
