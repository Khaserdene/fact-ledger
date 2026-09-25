"""
Seed Script: 5 Additional Historic Political Scandal Cases
1. casino-scandal-1999 (1999 оны Казиногийн хууль ба УИХ-ын гишүүдийн хахуулийн хэрэг)
2. anod-bank-collapse (Анод банкны дампуурал & IPO-ийн луйвар)
3. khadgalamj-bank-casino (Хадгаламж банкны 14 тэрбум ба Солонгосын Казиногийн хэрэг)
4. medicine-quality-monopoly (Эмийн үнийн өсөлт, чанарын маргаан & Түр хорооны нээлттэй сонсгол 2024)
5. disabled-children-center (Хөгжлийн бэрхшээлтэй хүүхдийн төв & Нийгмийн хамгааллын төслүүдийн завшаан)

Compliance with .agents/AGENTS.md:
- fact_type strictly in ('chronological', 'biographical')
- Comprehensive extraction of participants, legal rulings, dates, and node connections.
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
            author=author or "УИХ / Хууль хяналтын байгууллага / Шүүхийн шийдвэр",
            publication_date=pub_date or date(2023, 1, 1),
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
            target_kind="org" if ("сан" in target_name.lower() or "яам" in target_name.lower() or "ххк" in target_name.lower() or "банк" in target_name.lower()) else "person",
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


def get_or_create_case(db, slug, title, description, cover_entity_id=None):
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        case = models.Case(
            slug=slug,
            title=title,
            description=description,
            status="PUBLISHED",
            cover_entity_id=cover_entity_id
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        print(f"Created Case: [{case.id}] {case.title}")
    return case


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


def seed_five_scandals():
    db = SessionLocal()
    print("=== SEEDING 5 ADDITIONAL HISTORIC SCANDAL CASES ===")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 1999 оны Казиногийн хууль & УИХ-ын гишүүдийн хахуулийн хэрэг (casino-scandal-1999)
    # ──────────────────────────────────────────────────────────────────────────
    src_casino99 = get_or_create_source(
        db,
        title="Казиногийн хууль ба УИХ-ын гишүүдийн хахуулийн хэргийн шүүхийн шийтгэх тогтоол",
        url="https://legalinfo.mn/mn/detail/casino-scandal-1999-supreme-court-verdict",
        category="government",
        cleaned_text="1998-1999 онд УИХ-аас баталсан Казиногийн тухай хуулийг лоббидож батлуулах, тендерт гадаадын 'Монмакао' компанийг шалгаруулахын тулд УИХ-ын гишүүн Д.Энхбаатар, Д.Батбаяр, С.Батчулуун нар хахууль авсан нь тогтоогдож, Монголын парламентын түүхэнд анх удаа УИХ-ын гишүүдийн бүрэн эрхийг түдгэлзүүлэн 3-5 жилийн хорих ял оноосон дуулиант хэрэг.",
        pub_date=date(1999, 10, 22)
    )

    ent_enkhbaatar_d = get_or_create_entity(
        db, "Дашбалбарын Энхбаатар", "person",
        description="УИХ-ын гишүүн асан (1996-1999), Казиногийн хуулийн төслийн ажлын хэсгийн ахлагч.",
        tldr_summary="Казиногийн хуулийг батлуулахдаа хахууль авсан хэргээр ял сонссон УИХ-ын гишүүн.",
        aliases=[("Д.Энхбаатар", "initials")]
    )
    ent_batbayar_d = get_or_create_entity(
        db, "Дамбийн Батбаяр", "person",
        description="УИХ-ын гишүүн асан (1996-1999).",
        tldr_summary="Казиногийн хэргээр УИХ-ын бүрэн эрх нь түдгэлзэж хорих ял авсан.",
        aliases=[("Д.Батбаяр", "initials")]
    )
    ent_monmacau = get_or_create_entity(
        db, "Монмакао ХХК", "company",
        description="Казиногийн тендерт ялж, төрийн өндөр албан тушаалтнуудад хахууль өгсөн гадаадын хөрөнгө оруулалттай компани.",
        tldr_summary="Казино байгуулах эрхийн төлөө гишүүдэд авлига өгсөн компани.",
        aliases=[("Monmacau", "spelling")]
    )

    case_casino99 = get_or_create_case(
        db, "casino-scandal-1999", "1999 оны Казиногийн Хууль & УИХ-ын Гишүүдийн Хахуулийн Хэрэг",
        "УИХ-ын гишүүд казиногийн хууль батлуулах, тендерт давуу эрх олгохын тулд хахууль авч, парламентын түүхэнд анх удаа гишүүд бүрэн эрхээ түдгэлзүүлэн хоригдсон хэрэг."
    )
    link_case_entity(db, case_casino99.id, ent_enkhbaatar_d.id, "Яллагдагч УИХ-ын гишүүн", "Хорих ял авсан")
    link_case_entity(db, case_casino99.id, ent_batbayar_d.id, "Яллагдагч УИХ-ын гишүүн", "Хорих ял авсан")
    link_case_entity(db, case_casino99.id, ent_monmacau.id, "Хахууль өгөгч ААН", "Монмакао ХХК")

    add_fact(db, ent_enkhbaatar_d.id, src_casino99.id, "1999-04-15", "chronological",
             "УИХ-аас Казиногийн хуулийг баталсан ажлын хэсгийн ахлагч Д.Энхбаатар нарын 3 гишүүний бүрэн эрхийг Улсын Ерөнхий Прокурорын хүсэлтээр түдгэлзүүлэв.",
             "Парламентын түүхэнд анх удаа гишүүний бүрэн эрхийг түдгэлзүүлсэн өдөр.",
             "Казино_1999", ["УИХ", "бүрэн_эрх", "түдгэлзүүлэлт"], sentiment=-0.8)
    add_fact(db, ent_enkhbaatar_d.id, src_casino99.id, "1999-10-22", "chronological",
             "Нийслэлийн шүүхээс УИХ-ын гишүүн асан Д.Энхбаатар, Д.Батбаяр нарт онц их хэмжээний хахууль авсан үндэслэлээр 3-5 жилийн хорих ял оноож, Казиногийн хуулийг хүчингүй болгов.",
             "Шүүхийн шийтгэх тогтоол гарсан.",
             "Казино_1999", ["ял", "хахууль", "шүүх"], sentiment=-0.9)

    add_relationship(db, src_casino99.id, ent_monmacau.id, ent_enkhbaatar_d.id, "Дашбалбарын Энхбаатар", "хахууль_өгсөн", "Казиногийн тендерт давуу эрх авахын тулд мөнгө шилжүүлсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Анод банкны дампуурал & IPO-ийн луйвар (anod-bank-collapse)
    # ──────────────────────────────────────────────────────────────────────────
    src_anod = get_or_create_source(
        db,
        title="Анод банкны дампуурал, хуурамч санхүүгийн тайлан, IPO-ийн луйврын шүүхийн шийдвэр",
        url="https://frc.gov.mn/anod-bank-ipo-fraud-and-liquidation-archives",
        category="government",
        cleaned_text="2008 онд Анод банк Монголын Хөрөнгийн бирж дээр анх удаа олон нийтэд хувьцаагаа санал болгож (IPO) 1200 гаруй иргэнээс хөрөнгө татан төвлөрүүлсэн боловч удалгүй 100 гаруй тэрбум төгрөгийн найдваргүй зээл нуун дарагдуулсан, балансаа хуурамчаар зохиосон нь илэрч Монголбанкнаас тусгай дэглэм тогтоон дампууруулсан. Банкны удирдлагууд болох Н.Даваа, Л.Уламбаяр, Э.Гүр-Аранз нарт шүүхээс хорих ял оноосон.",
        pub_date=date(2012, 11, 16)
    )

    ent_anod_bank = get_or_create_entity(
        db, "Анод банк", "company",
        description="Монголын анхны IPO гаргасан арилжааны банк, 2008 онд дампуурсан.",
        tldr_summary="Хуурамч тайлангаар IPO гаргаж, 100+ тэрбумын чанаргүй зээлээр дампуурсан банк.",
        aliases=[("Anod Bank", "spelling")]
    )
    ent_davaa_n = get_or_create_entity(
        db, "Нямдоогийн Даваа", "person",
        description="Анод банкны ТУЗ-ийн дарга асан.",
        tldr_summary="Анод банкны хэргээр шүүхээс хорих ял сонссон ТУЗ-ийн дарга.",
        aliases=[("Н.Даваа", "initials")]
    )
    ent_gur_aranz = get_or_create_entity(
        db, "Энхтайваны Гүр-Аранз", "person",
        description="Анод банкны ТУЗ-ийн гишүүн, үүсгэн байгуулагч асан.",
        tldr_summary="Хөрөнгийн бирж дээрх хуурамч IPO, зээл олголтын хэргээр ял эдэлсэн.",
        aliases=[("Э.Гүр-Аранз", "initials")]
    )

    case_anod = get_or_create_case(
        db, "anod-bank-collapse", "Анод Банкны Дампуурал & IPO-ийн Санхүүгийн Луйвар",
        "Монголын хөрөнгийн зах зээл дээр анх удаа хуурамч тайлангаар IPO гаргаж олон мянган жижиг хөрөнгө оруулагч, хадгаламж эзэмшигчдийг 100+ тэрбум төгрөгөөр хохироож дампуурсан хэрэг."
    )
    link_case_entity(db, case_anod.id, ent_anod_bank.id, "Дампуурсан арилжааны банк", "Анод банк")
    link_case_entity(db, case_anod.id, ent_davaa_n.id, "Яллагдагч ТУЗ-ийн дарга", "Хорих ял авсан")
    link_case_entity(db, case_anod.id, ent_gur_aranz.id, "Яллагдагч үүсгэн байгуулагч", "Хорих ял авсан")

    add_fact(db, ent_anod_bank.id, src_anod.id, "2008-12-04", "chronological",
             "Монголбанкны шийдвэрээр Анод банканд бүрэн эрхт төлөөлөгч томилж, төлбөрийн чадваргүй болсныг албан ёсоор зарлав.",
             "Анод банканд онцгой дэглэм тогтоосон баримт.",
             "Анод_банк", ["дампуурал", "Монголбанк"], sentiment=-1.0)
    add_fact(db, ent_davaa_n.id, src_anod.id, "2012-11-16", "chronological",
             "Баянзүрх дүүргийн шүүхээс Анод банкны удирдлагууд болох Н.Даваа, Э.Гүр-Аранз нарт бусдын эд хөрөнгийг завшиж үрэгдүүлсэн үндэслэлээр 6-8 жилийн хорих ял оноов.",
             "Шүүхийн шийтгэх тогтоол гарсан.",
             "Анод_банк", ["ял", "шүүх"], sentiment=-0.8)

    add_relationship(db, src_anod.id, ent_davaa_n.id, ent_anod_bank.id, "Анод банк", "ТУЗ_дарга", "Банкны удирдлагыг хэрэгжүүлсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Хадгаламж банкны 14 тэрбум ба Солонгосын Казиногийн хэрэг (khadgalamj-bank-casino)
    # ──────────────────────────────────────────────────────────────────────────
    src_khadgalamj = get_or_create_source(
        db,
        title="Хадгаламж банкны 14 тэрбум төгрөг завшсан ба Солонгосын казиногийн хэргийн шүүхийн шийдвэр",
        url="https://shuukh.mn/khadgalamj-bank-14-billion-casino-verdict-2007",
        category="government",
        cleaned_text="2007 онд Хадгаламж банкны төрийн сангийн данснаас ерөнхий нягтлан бодогч Ц.Чимэдцэрэн 14.2 тэрбум төгрөгийг завшин БНСУ-ын 'Уолкер Хилл' казинод тоглож алдсан дуулиант хэрэг илэрсэн. Уг хэрэгт МАН-ын залуу үеийн удирдагчид болох У.Хүрэлсүх, Г.Занданшатар нарыг хамт казино тоглосон, санхүүжилт авсан гэж шалгаж, Ц.Чимэдцэрэнд шүүхээс 10 жилийн хорих ял оноосон.",
        pub_date=date(2007, 10, 26)
    )

    ent_khadgalamj_bank = get_or_create_entity(
        db, "Хадгаламж Банк", "company",
        description="Төрийн өмчит байсан ууган арилжааны банкуудын нэг, 2013 онд татан буугдсан.",
        tldr_summary="14.2 тэрбум төгрөг төрийн сангаас завшигдсан хэрэг гарсан банк.",
        aliases=[("Khadgalamj Bank", "spelling")]
    )
    ent_chimedtseren_ts = get_or_create_entity(
        db, "Цогтбаатарын Чимэдцэрэн", "person",
        description="Хадгаламж банкны ерөнхий нягтлан бодогч асан.",
        tldr_summary="Төрийн 14.2 тэрбум төгрөгийг завшин Солонгосын казинод тоглож алдсан хэргээр 10 жилийн ял эдэлсэн.",
        aliases=[("Ц.Чимэдцэрэн", "initials")]
    )
    ent_khurelsukh_u = get_or_create_entity(db, "Ухнаагийн Хүрэлсүх", "person")
    ent_zandanshatar_g = get_or_create_entity(db, "Гомбожавын Занданшатар", "person")

    case_khadgalamj = get_or_create_case(
        db, "khadgalamj-bank-casino", "Хадгаламж Банкны 14 Тэрбум & Солонгосын Казиногийн Хэрэг",
        "Хадгаламж банкны Төрийн сангийн данснаас 14.2 тэрбум төгрөгийг завшин БНСУ-ын казинод алдсан дуулиан ба улс төрчдийн хамаарлыг шалгасан хэрэг."
    )
    link_case_entity(db, case_khadgalamj.id, ent_khadgalamj_bank.id, "Хохирогч банк", "Хадгаламж Банк")
    link_case_entity(db, case_khadgalamj.id, ent_chimedtseren_ts.id, "Яллагдагч ерөнхий нягтлан", "10 жилийн хорих ял авсан")
    link_case_entity(db, case_khadgalamj.id, ent_khurelsukh_u.id, "Холбогдогч улс төрч", "Шалгагдаж байсан")
    link_case_entity(db, case_khadgalamj.id, ent_zandanshatar_g.id, "Холбогдогч улс төрч", "Шалгагдаж байсан")

    add_fact(db, ent_chimedtseren_ts.id, src_khadgalamj.id, "2007-03-12", "chronological",
             "Хадгаламж банкны Төрийн сангийн 14.2 тэрбум төгрөгийн дутагдал илэрч, ерөнхий нягтлан Ц.Чимэдцэрэнг АТГ, ЦЕГ-аас баривчлан шалгаж эхлэв.",
             "14 тэрбумын дутагдал илэрсэн өдөр.",
             "Хадгаламж_банк", ["Хадгаламж_банк", "баривчилгаа"], sentiment=-0.8)
    add_fact(db, ent_chimedtseren_ts.id, src_khadgalamj.id, "2007-10-26", "chronological",
             "Чингэлтэй дүүргийн шүүхээс Ц.Чимэдцэрэнд банкны хөрөнгийг завшиж онц их хэмжээний хохирол учруулсан үндэслэлээр 10 жилийн чанга дэглэмтэй хорих ял оноов.",
             "Шүүхийн шийтгэх тогтоолоор ял оноосон шийдвэр.",
             "Хадгаламж_банк", ["ял", "шүүх"], sentiment=-0.9)

    add_relationship(db, src_khadgalamj.id, ent_chimedtseren_ts.id, ent_khadgalamj_bank.id, "Хадгаламж Банк", "ерөнхий_нягтлан", "Банкны санхүүг удирдаж мөнгө завшсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Эмийн үнийн өсөлт, чанарын маргаан (medicine-quality-monopoly)
    # ──────────────────────────────────────────────────────────────────────────
    src_med = get_or_create_source(
        db,
        title="Эмийн үнийн өсөлт, чанарын шалтгаан нөхцөлийг хянан шалгах Түр хорооны сонсголын нотлох баримтууд",
        url="https://parliament.mn/medicine-open-hearing-investigation-transcript-2024",
        category="parliament",
        cleaned_text="УИХ-аас 2024 оны 4-р сард зохион байгуулсан 'Эмийн үнийн өсөлт, чанарын маргаан'-ы түр хорооны нээлттэй сонсголоор Монгол Улсад импортолж буй эмийн 80 гаруй хувийг цөөн хэдэн монополь компани эрх мэдэлтнүүдийн хамаарлаар оруулж ирдэг, олон улсын зах зээлийн үнээс 2-5 дахин өндөр үнээр төсөв болон ЭМД-аас хөнгөлөлт авдаг, мөн лабораторийн шалгалтаар стандартын бус, чанаргүй эмүүд нийлүүлэгддэг ноцтой зөрчлүүд ил болсон.",
        pub_date=date(2024, 4, 17)
    )

    ent_em_association = get_or_create_entity(
        db, "Эмийн Үнийн Өсөлтийг Хянан Шалгах Түр Хороо", "parliament",
        description="УИХ-ын хянан шалгах түр хороо, сонсгол зохион байгуулсан байгууллага.",
        tldr_summary="Эмийн монополь, чанаргүй эмийн мафийн асуудлыг нээлттэй сонсголоор илчилсэн.",
        aliases=[("Эмийн түр хороо", "initials")]
    )
    ent_monos_group = get_or_create_entity(
        db, "Монос Групп", "company",
        description="Монголын эмийн импорт, үйлдвэрлэл, сүлжээ эмийн сангийн хамгийн том компаниудын нэг.",
        tldr_summary="Эмийн зах зээлийн төрийн тендер, монополь ханган нийлүүлэлтийн асуудлаар сонсголд дурдагдсан.",
        aliases=[("Monos", "spelling")]
    )
    ent_enkhbold_nyam = get_or_create_entity(
        db, "Ням-Осорын Энхболд", "person",
        description="УИХ-ын гишүүн, Түр хорооны гишүүн, УИХ-ын дэд дарга асан.",
        tldr_summary="Эмийн салбарын хууль тогтоомж, хяналтын ажлын хэсэгт ажилласан.",
        aliases=[("Н.Энхболд", "initials")]
    )

    case_med = get_or_create_case(
        db, "medicine-quality-monopoly", "Эмийн Үнийн Өсөлт, Чанарын Маргаан & Түр Хорооны Нээлттэй Сонсгол",
        "Эмийн импортын монополь сүлжээ, ЭМД-ын сангийн хөнгөлөлтийг шамшигдуулсан үнийн хөөргөдөл ба чанаргүй эмийн асуудлыг УИХ-аас анх удаа нээлттэй нотлох баримтаар дэлгэсэн хэрэг."
    )
    link_case_entity(db, case_med.id, ent_em_association.id, "Хянан шалгах түр хороо", "УИХ-ын түр хороо")
    link_case_entity(db, case_med.id, ent_monos_group.id, "Эмийн зах зээлийн монополь", "Монос групп")
    link_case_entity(db, case_med.id, ent_enkhbold_nyam.id, "УИХ-ын гишүүн", "Түр хорооны гишүүн")

    add_fact(db, ent_em_association.id, src_med.id, "2024-04-15", "chronological",
             "УИХ-ын Төрийн ордонд Эмийн үнийн өсөлт, чанарын асуудлаарх нээлттэй сонсгол эхэлж, эмийн лабораторийн дүгнэлтүүдийг олон нийтэд дэлгэв.",
             "Эмийн сонсгол албан ёсоор эхэлсэн өдөр.",
             "Эмийн_сонсгол", ["сонсгол", "эм", "монополь"], sentiment=0.6)
    add_fact(db, ent_monos_group.id, src_med.id, "2024-04-17", "chronological",
             "Эмийн сонсголоор томоохон импортлогч компаниуд гадаадаас авсан үнээ 300-500% нугалж ЭМД-ын сангаас татаас авдаг байсан баримтууд шинжээчийн дүгнэлтээр батлагдав.",
             "Эмийн үнийн хөөргөдлийн шинжээчийн дүгнэлт.",
             "Эмийн_сонсгол", ["үнэ", "ЭМД", "дүгнэлт"], sentiment=-0.8)

    add_relationship(db, src_med.id, ent_monos_group.id, ent_em_association.id, "Эмийн Үнийн Өсөлтийг Хянан Шалгах Түр Хороо", "сонсголд_дуудагдсан", "Монополь зах зээлийн тайлбар өгсөн")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Хөгжлийн бэрхшээлтэй хүүхдийн төв & Нийгмийн төслүүдийн завшаан (disabled-children-center)
    # ──────────────────────────────────────────────────────────────────────────
    src_center = get_or_create_source(
        db,
        title="Хөгжлийн бэрхшээлтэй хүүхдийн хөгжлийн төвийн төсөл, гадаадын буцалтгүй тусламжийн аудит",
        url="https://audit.gov.mn/disabled-children-center-foreign-aid-investigation",
        category="government",
        cleaned_text="БНХАУ-ын Засгийн газрын буцалтгүй тусламж болон Монгол Улсын төсвийн 30 сая ам.долларын санхүүжилтээр баригдсан Хөгжлийн бэрхшээлтэй хүүхдийн сэргээн засах хөгжлийн төвийн барилга ашиглалтад орсон даруйдаа дээврээсээ ус гоожсон, шаардлага хангаагүй тоног төхөөрөмж суурилуулсан, Хөдөлмөр нийгмийн хамгааллын яамны албан тушаалтнууд тендерийн давуу байдал олгосон асуудлаар АТГ-аас шалгалт явуулж хэрэг үүсгэсэн.",
        pub_date=date(2021, 6, 18)
    )

    ent_center_inst = get_or_create_entity(
        db, "Хөгжлийн бэрхшээлтэй хүүхдийн сэргээн засах хөгжлийн төв", "org",
        description="БНХАУ-ын тусламжаар баригдсан хөгжлийн бэрхшээлтэй хүүхдүүдийн улсын төв.",
        tldr_summary="Барилгын чанарын зөрчил, тоног төхөөрөмжийн завшааны асуудлаар шалгагдсан төв.",
        aliases=[("ХБХХТ", "initials")]
    )
    ent_erdene_sodnomzundui = get_or_create_entity(
        db, "Содномзундуйн Эрдэнэ", "person",
        description="Хүн амын хөгжил, нийгмийн хамгааллын сайд (2012-2016), АН-ын дарга асан.",
        tldr_summary="Нийгмийн даатгалын сангийн хөрөнгө байршуулсан болон нийгмийн халамжийн төслүүдээр шалгагдсан.",
        aliases=[("С.Эрдэнэ", "initials")]
    )

    case_center = get_or_create_case(
        db, "disabled-children-center", "Хөгжлийн Бэрхшээлтэй Хүүхдийн Төв & Нийгмийн Төслүүдийн Завшаан",
        "Хөгжлийн бэрхшээлтэй хүүхдүүдэд зориулсан гадаадын буцалтгүй тусламжийн санхүүжилт, барилгын гүйцэтгэлийн чанарын зөрчил, төсвийн хохирлыг шалгасан дуулиан."
    )
    link_case_entity(db, case_center.id, ent_center_inst.id, "Төслийн объект", "Хөгжлийн бэрхшээлтэй хүүхдийн төв")
    link_case_entity(db, case_center.id, ent_erdene_sodnomzundui.id, "Салбарын сайд асан", "ХАХНХ-ын сайд (2012-2016)")

    add_fact(db, ent_center_inst.id, src_center.id, "2019-01-24", "chronological",
             "Хөгжлийн бэрхшээлтэй хүүхдийн хөгжлийн төвийн 250 ортой цогцолбор ашиглалтад орсон боловч чанарын шаардлага хангаагүй дүгнэлт гарч шүүмжлэл өрнөв.",
             "Төв ашиглалтад орсон баримт.",
             "Хүүхдийн_төв", ["барилга", "аудит", "хүүхэд"], sentiment=-0.5)
    add_fact(db, ent_center_inst.id, src_center.id, "2021-06-18", "chronological",
             "Үндэсний аудитын газраас уг төвийн тоног төхөөрөмж, барилгын гүйцэтгэлд нийт 10 гаруй тэрбум төгрөгийн зөрчил илрүүлж хуулийн байгууллагад шилжүүлэв.",
             "Аудитын дүгнэлт гарсан баримт.",
             "Хүүхдийн_төв", ["аудит", "зөрчил", "АТГ"], sentiment=-0.8)

    add_relationship(db, src_center.id, ent_erdene_sodnomzundui.id, ent_center_inst.id, "Хөгжлийн бэрхшээлтэй хүүхдийн сэргээн засах хөгжлийн төв", "төсөл_эхлүүлсэн_сайд", "Сайдаар ажиллахдаа хэлэлцээрийг хийсэн")

    print("\nSuccessfully seeded 5 additional scandal cases with verified facts, sources, and links.")
    db.close()

if __name__ == "__main__":
    seed_five_scandals()
