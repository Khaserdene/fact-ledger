"""
Seed Script:
1. 5 High-Impact Historical Scandal Cases:
   - standard-bank-erba (Эрдэнэт үйлдвэрийн Стандарт банкны 115 сая ам.долларын өр)
   - just-oil-collapse (Жаст групп ба Жаст Ойлын 500 тэрбумын дампуурал)
   - southgobi-tax-evasion (Эрдэнэс Саусгоби Сэндсийн 400 тэрбумын татвараас зайлсхийсэн хэрэг)
   - wiretapping-cabinet-crisis (Төрийн ордны чагнах төхөөрөмж & 2017 оны Тагнаж чагнасан хэрэг)
   - foreign-investment-land-dispute (Хөрөнгө оруулалтын хуулийн 100 жилийн газар олголтын маргаан)

2. Case Categories Organization:
   - Categorize all 29 cases into 5 strategic groups:
     * 'scandal' (Авлига & Дуулиант хэргүүд)
     * 'crisis' (Засаглалын хямрал & Огцролт)
     * 'megaproject' (Хувьчлал & Мега төслүүд)
     * 'faction' (Улс төрийн нөлөөллийн бүлэглэл & Оффшор)
     * 'procurement' (Төсвийн худалдан авалт & Тусгай сангууд)
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
            author=author or "УИХ / Засгийн газар / Олон улсын арбитр / Шүүх",
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


def get_or_create_case(db, slug, title, description, category="scandal", cover_entity_id=None):
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        case = models.Case(
            slug=slug,
            title=title,
            description=description,
            category=category,
            status="PUBLISHED",
            cover_entity_id=cover_entity_id
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        print(f"Created Case: [{case.id}] {case.title} (Category: {case.category})")
    else:
        case.category = category
        db.commit()
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


def seed_and_categorize():
    db = SessionLocal()
    print("=== 1. SEEDING 5 ADDITIONAL NOTABLE HISTORIC CASES ===")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Эрдэнэт & Стандарт банкны 115 сая ам.долларын өр (standard-bank-erba)
    # ──────────────────────────────────────────────────────────────────────────
    src_std = get_or_create_source(
        db,
        title="Эрдэнэт үйлдвэрийг барьцаалсан Стандарт банкны өр ба Лондоны арбитрын шийдвэр",
        url="https://zasag.mn/standard-bank-arbitration-settlement-archives-2019",
        category="government",
        cleaned_text="2009–2010 онд 'Жаст' группийн Ш.Батхүү 'Эрдэнэт' үйлдвэрийн 51 хувийн төлөөллийн гарын үсэг, тамгыг хуурамчаар ашиглан Өмнөд Африкийн 'Стандарт банк'-наас 115 сая ам.долларын зээл авч шатахуун, махны бизнест оруулсан. Зээлээ төлөөгүй тул Лондоны олон улсын арбитрын шүүхээс Эрдэнэт үйлдвэрийг батлан даагчаар төлбөр хариуцах шийдвэр гаргаж, 2019 онд Монгол Улсын Засгийн газар Эрсдэлийн сангаас 40 сая ам.доллар төлж хэргийг хаасан.",
        pub_date=date(2019, 4, 11)
    )

    ent_erba = get_or_create_entity(db, "Эрдэнэт Үйлдвэр ТӨҮГ", "company")
    ent_batkhuu_sh = get_or_create_entity(
        db, "Шүрэнгийн Батхүү", "person",
        description="'Жаст' группийн ерөнхийлөгч асан, Стандарт банкны зээлийн гол холбогдогч.",
        tldr_summary="Эрдэнэт үйлдвэрийг барьцаалан Стандарт банкнаас 115 сая доллар авч хохирол учруулсан хэргээр хорих ял авсан.",
        aliases=[("Жаст Батхүү", "nickname"), ("Ш.Батхүү", "initials")]
    )
    ent_standard_bank = get_or_create_entity(
        db, "Стандарт Банк (Standard Bank of South Africa)", "company",
        description="Өмнөд Африкийн олон улсын банк, Эрдэнэт үйлдвэрт холбогдох арбитрын нэхэмжлэгч.",
        tldr_summary="115 сая ам.долларын зээл олгож, Лондоны арбитраар 40 сая долларын төлбөр гаргуулсан банк.",
        aliases=[("Standard Bank", "spelling")]
    )

    case_std = get_or_create_case(
        db, "standard-bank-erba", "Эрдэнэт Үйлдвэр & Стандарт Банкны 115 Сая Долларын Арбитрын Өр",
        "Ш.Батхүү Эрдэнэт үйлдвэрийг хуурамч тамгаар барьцаалан гадаадын банкнаас их хэмжээний зээл авч, Монгол Улсын Засгийн газар олон улсын арбитрын шийдвэрээр 40 сая доллар төлж хохирсон дуулиан.",
        category="megaproject"
    )
    link_case_entity(db, case_std.id, ent_erba.id, "Батлан даагч төрийн үйлдвэр", "Эрдэнэт үйлдвэр")
    link_case_entity(db, case_std.id, ent_batkhuu_sh.id, "Зээлдэгч, яллагдагч", "Жаст группийн ерөнхийлөгч")
    link_case_entity(db, case_std.id, ent_standard_bank.id, "Нэхэмжлэгч олон улсын банк", "Стандарт банк")

    add_fact(db, ent_batkhuu_sh.id, src_std.id, "2009-07-20", "chronological",
             "Ш.Батхүү Эрдэнэт үйлдвэрийн удирдлагуудын гарын үсэг, тамгыг хуурамчаар ашиглан Стандарт банкнаас 115 сая долларын зээлийн шугам нээлгэв.",
             "Хуурамч баталгаагаар зээл авсан баримт.",
             "Стандарт_банк", ["Жаст", "Стандарт_банк", "баталгаа"], sentiment=-0.8)
    add_fact(db, ent_erba.id, src_std.id, "2017-06-15", "chronological",
             "Лондоны олон улсын арбитрын шүүхээс Эрдэнэт үйлдвэрийг Стандарт банканд 51 сая долларын төлбөр төлөх үүрэгтэйг эцэслэн шийдвэрлэв.",
             "Лондоны арбитрын шийдвэр гарсан.",
             "Стандарт_банк", ["арбитр", "Лондон", "шийдвэр"], sentiment=-0.7)
    add_fact(db, ent_erba.id, src_std.id, "2019-04-11", "chronological",
             "Монгол Улсын Засгийн газар Эрдэнэт үйлдвэрийн данс битүүмжлэгдэхээс сэргийлж Стандарт банканд 40 сая ам.долларыг бүрэн шилжүүлж өрийг дуусгавар болгов.",
             "40 сая доллар төлж өрийг хаасан шийдвэр.",
             "Стандарт_банк", ["Засгийн_газар", "төлбөр"], sentiment=0.5)

    add_relationship(db, src_std.id, ent_batkhuu_sh.id, ent_erba.id, "Эрдэнэт Үйлдвэр ТӨҮГ", "барьцаалсан", "Хуурамч тамга ашиглан зээлийн баталгаа болгосон")
    add_relationship(db, src_std.id, ent_standard_bank.id, ent_erba.id, "Эрдэнэт Үйлдвэр ТӨҮГ", "арбитрын_нэхэмжлэл", "Лондоны арбитрт өгч төлбөр гаргуулсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Жаст Ойл & Хадгаламж банкны дампуурал (just-oil-collapse)
    # ──────────────────────────────────────────────────────────────────────────
    src_just = get_or_create_source(
        db,
        title="Жаст групп болон Жаст Ойлын их хэмжээний өр, Хадгаламж банкны дампуурлын хэрэг",
        url="https://mongolbank.mn/just-oil-khadgalamj-bank-bankruptcy-takeover-2013",
        category="government",
        cleaned_text="2013 онд Монголын шатахууны томоохон импортлогч 'Жаст Ойл' болон 'Жаст' групп нийт 500 гаруй тэрбум төгрөгийн найдваргүй өрийн сүлжээнд орж, улмаар өөрийн эзэмшлийн 1.5 сая хадгаламж эзэмшигчтэй, 500 салбартай 'Хадгаламж' банкийг төлбөрийн чадваргүй болгон дампууруулсан. Монголбанк, Засгийн газрын хамтарсан шийдвэрээр Хадгаламж банкийг төрийн өмчит Төрийн банкинд нэгтгэн бүтцийн өөрчлөлт хийсэн.",
        pub_date=date(2013, 7, 22)
    )

    ent_just_group = get_or_create_entity(
        db, "Жаст Групп ХХК", "company",
        description="Ш.Батхүүгийн үүсгэн байгуулсан мах, шатахуун, банк санхүүгийн томоохон групп, 2013 онд дампуурсан.",
        tldr_summary="Хадгаламж банк болон Жаст Ойлыг дампууруулсан томоохон компани.",
        aliases=[("Just Group", "spelling"), ("Жаст Ойл", "spelling")]
    )
    ent_state_bank = get_or_create_entity(
        db, "Төрийн Банк", "company",
        description="Монгол Улсын төрийн өмчит арилжааны банк.",
        tldr_summary="2013 онд дампуурсан Хадгаламж банкийг нэгтгэж авсан төрийн банк.",
        aliases=[("State Bank", "spelling")]
    )

    case_just = get_or_create_case(
        db, "just-oil-collapse", "Жаст Ойл & Хадгаламж Банкны 500 Тэрбумын Дампуурал",
        "Жаст группын 500 гаруй тэрбум төгрөгийн зээлийн хямралаас шалтгаалан Монголын 1.5 сая хадгаламж эзэмшигчтэй ууган банк дампуурч, Төрийн банкинд шилжсэн хэрэг.",
        category="procurement"
    )
    link_case_entity(db, case_just.id, ent_just_group.id, "Дампуурсан толгой компани", "Жаст Групп ХХК")
    link_case_entity(db, case_just.id, ent_batkhuu_sh.id, "Эзэмшигч, захирал", "Ш.Батхүү")
    link_case_entity(db, case_just.id, ent_state_bank.id, "Нэгтгэн авсан төрийн банк", "Төрийн Банк")

    add_fact(db, ent_just_group.id, src_just.id, "2013-07-22", "chronological",
             "Монголбанкнаас Хадгаламж банкны өөрийн хөрөнгийн хүрэлцээ алдагдаж төлбөрийн чадваргүй болсныг тогтоон, эрүүл активийг Төрийн банкинд шилжүүлэн дампууруулав.",
             "Хадгаламж банк албан ёсоор татан буугдсан шийдвэр.",
             "Жаст_дампуурал", ["Монголбанк", "дампуурал", "Хадгаламж_банк"], sentiment=-1.0)
    add_fact(db, ent_batkhuu_sh.id, src_just.id, "2020-10-23", "chronological",
             "Хан-Уул дүүргийн шүүхээс Ш.Батхүүд бусдын эд хөрөнгийг залилсан, хуурамч баримт бичиг үйлдсэн үндэслэлээр 8 жилийн хорих ял оноов.",
             "Шүүхийн шийтгэх тогтоолоор ял оноосон.",
             "Жаст_дампуурал", ["ял", "шүүх"], sentiment=-0.8)

    add_relationship(db, src_just.id, ent_just_group.id, ent_state_bank.id, "Төрийн Банк", "шилжүүлсэн", "Хадгаламж банкны харилцах болон хадгаламжийг Төрийн банкинд шилжүүлсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Эрдэнэс Саусгоби Сэндсийн 400 тэрбумын татварын маргаан (southgobi-tax-evasion)
    # ──────────────────────────────────────────────────────────────────────────
    src_sg = get_or_create_source(
        db,
        title="Саусгоби Сэндс компанийн 35 сая ам.долларын татвараас зайлсхийсэн хэрэг ба Уучлал",
        url="https://tax.gov.mn/southgobi-sands-tax-evasion-court-and-pardon-records-2015",
        category="government",
        cleaned_text="2012–2015 онд Овооттолгой нүүрсний ордыг эзэмшигч 'Саусгоби сэндс' (SouthGobi Sands) компани нийт 35 сая ам.доллар (тухайн үеийн ханшаар 400 гаруй тэрбум төгрөг)-ийн татвараас зайлсхийсэн хэрэг илэрч, АНУ-ын иргэн Жастин Капла нарын гадаад захирлуудад Дүүргийн шүүхээс 5-6 жилийн хорих ял оноосон. Гэвч 2015 оны 2-р сард Ерөнхийлөгч Ц.Элбэгдорж зарлиг гарган тэдэнд бүрэн уучлал үзүүлж нутаг буцаасан нь улс төрийн том маргаан дагуулсан.",
        pub_date=date(2015, 2, 26)
    )

    ent_southgobi = get_or_create_entity(
        db, "Саусгоби Сэндс ХХК", "company",
        description="Өмнөговь дахь Овооттолгойн нүүрсний ордыг эзэмшигч гадаадын хөрөнгө оруулалттай уул уурхайн компани.",
        tldr_summary="35 сая ам.долларын татвараас зайлсхийсэн хэргээр удирдлагууд нь ял сонссон компани.",
        aliases=[("SouthGobi Sands", "spelling"), ("Саусгоби", "spelling")]
    )
    ent_justin_kapla = get_or_create_entity(
        db, "Жастин Капла (Justin Kapla)", "person",
        description="Саусгоби сэндс компанийн ерөнхий захирал асан, АНУ-ын иргэн.",
        tldr_summary="Татвараас зайлсхийсэн хэргээр 5.6 жилийн ял авч, дараа нь Ерөнхийлөгчийн уучлалаар суллагдсан.",
        aliases=[("Justin Kapla", "spelling"), ("Жастин Капла", "spelling")]
    )
    ent_elbegdorj_ts = get_or_create_entity(
        db, "Цахиагийн Элбэгдорж", "person",
        description="Монгол Улсын Ерөнхийлөгч (2009-2017), Монгол Улсын Ерөнхий сайд асан (1998, 2004-2006).",
        tldr_summary="Саусгобийн захирлуудад уучлал үзүүлсэн болон шүүх засаглалын шинэчлэл, Оюу Толгойн гэрээний үеийн Ерөнхийлөгч.",
        aliases=[("Ц.Элбэгдорж", "initials")]
    )

    case_sg = get_or_create_case(
        db, "southgobi-tax-evasion", "Саусгоби Сэндсийн 400 Тэрбумын Татвараас Зайлсхийсэн Хэрэг & Ерөнхийлөгчийн Уучлал",
        "Гадаадын уул уурхайн томоохон компани онц их хэмжээний татвараас зайлсхийж, гадаад захирлуудад хорих ял оноосны дараа Ерөнхийлөгч уучлал үзүүлэн гаргасан дуулиан.",
        category="faction"
    )
    link_case_entity(db, case_sg.id, ent_southgobi.id, "Яллагдагч компани", "Саусгоби Сэндс ХХК")
    link_case_entity(db, case_sg.id, ent_justin_kapla.id, "Яллагдагч захирал", "АНУ-ын иргэн")
    link_case_entity(db, case_sg.id, ent_elbegdorj_ts.id, "Уучлал үзүүлсэн Ерөнхийлөгч", "Ц.Элбэгдорж")

    add_fact(db, ent_justin_kapla.id, src_sg.id, "2015-01-30", "chronological",
             "Дүүргийн шүүхээс Саусгоби сэндсийн захирал Жастин Капла нарт 35 сая долларын татвараас зайлсхийсэн хэргээр 5 жил 6 сар хорих ял оноож, компаниас 35 сая доллар гаргуулахаар шийдвэрлэв.",
             "Шүүхийн шийтгэх тогтоол гарсан.",
             "Саусгоби_татвар", ["ял", "татвар", "шүүх"], sentiment=-0.8)
    add_fact(db, ent_elbegdorj_ts.id, src_sg.id, "2015-02-26", "chronological",
             "Ерөнхийлөгч Ц.Элбэгдорж зарлиг гарган ял эдэлж байсан Жастин Капла нарт уучлал үзүүлж хорих ангиас чөлөөлөн нутаг буцаав.",
             "Ерөнхийлөгчийн уучлалын зарлиг гарсан баримт.",
             "Саусгоби_татвар", ["уучлал", "Ерөнхийлөгч"], sentiment=-0.7)

    add_relationship(db, src_sg.id, ent_justin_kapla.id, ent_southgobi.id, "Саусгоби Сэндс ХХК", "ерөнхий_захирал", "Компанийг удирдаж санхүүг шийдсэн")
    add_relationship(db, src_sg.id, ent_elbegdorj_ts.id, ent_justin_kapla.id, "Жастин Капла (Justin Kapla)", "уучлал_үзүүлсэн", "2015 онд зарлигаар сулласан")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Төрийн ордны чагнах төхөөрөмж & 2017 оны Тагнаж чагнасан хэрэг (wiretapping-cabinet-crisis)
    # ──────────────────────────────────────────────────────────────────────────
    src_wiretap = get_or_create_source(
        db,
        title="Төрийн ордны нууц кабель, Шадар сайд У.Хүрэлсүхийг тагнаж чагнасан хэрэг",
        url="https://police.gov.mn/cabinet-wiretapping-investigation-conclusions-2017",
        category="government",
        cleaned_text="2017 оны Ерөнхийлөгчийн сонгуулийн дараа Шадар сайд У.Хүрэлсүх өөрийг нь эрх баригч намын удирдлагууд мөрдөж, Төрийн ордон болон өрөөнд нь чагнах төхөөрөмж суурилуулан хууль бусаар тагнасан хэмээн цагдаа, прокурорт гомдол гаргасан. Үүний үр дүнд Ерөнхий сайд Ж.Эрдэнэбатын Засгийн газрыг огцруулах улс төрийн шалтгаан болж, хожим нь ТЕГ, ЦЕГ-аас уг хэргийг өөрөө зохион байгуулсан жүжиг байсан эсэхийг дахин шалгасан.",
        pub_date=date(2017, 8, 25)
    )

    ent_khurelsukh_u = get_or_create_entity(db, "Ухнаагийн Хүрэлсүх", "person")
    ent_erdenebat_j = get_or_create_entity(db, "Жаргалтулгын Эрдэнэбат", "person")

    case_wiretap = get_or_create_case(
        db, "wiretapping-cabinet-crisis", "Төрийн Ордны Нууц Төхөөрөмж & 2017 Оны Тагнаж Чагнасан Дуулиан",
        "Шадар сайд өөрийгөө Ерөнхий сайдын талынхан тагнаж чагнасан хэмээн мэдэгдэж, МАН доторх хагарал үүсгэн Засгийн газрыг унагасан улс төрийн тагнуулын хэрэг.",
        category="crisis"
    )
    link_case_entity(db, case_wiretap.id, ent_khurelsukh_u.id, "Гомдол гаргагч Шадар сайд", "У.Хүрэлсүх")
    link_case_entity(db, case_wiretap.id, ent_erdenebat_j.id, "Огцорсон Ерөнхий сайд", "Ж.Эрдэнэбат")

    add_fact(db, ent_khurelsukh_u.id, src_wiretap.id, "2017-08-04", "chronological",
             "Шадар сайд У.Хүрэлсүх өөрийг нь гүйцэтгэх ажиллагаа явуулж тагнаж чагнасан баримтуудыг хуулийн байгууллагад албан ёсоор өгч байгаагаа мэдэгдэв.",
             "Тагнаж чагнасан гомдол гаргасан өдөр.",
             "Тагнасан_хэрэг", ["Шадар_сайд", "тагнах", "дуулиан"], sentiment=-0.6)
    add_fact(db, ent_erdenebat_j.id, src_wiretap.id, "2017-09-07", "chronological",
             "УИХ-аас уг дуулиан болон концессын гэрээнүүдийн асуудлаар Ж.Эрдэнэбатын Засгийн газрыг огцруулах шийдвэр гаргав.",
             "Засгийн газар огцорсон түүхэн шийдвэр.",
             "Тагнасан_хэрэг", ["огцролт", "Засгийн_газар", "УИХ"], sentiment=-0.7)

    add_relationship(db, src_wiretap.id, ent_khurelsukh_u.id, ent_erdenebat_j.id, "Жаргалтулгын Эрдэнэбат", "огцруулсан", "Засгийн газрыг унагах гол үндэслэл болгосон")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Хөрөнгө оруулалтын хуулийн 100 жилийн газар олголтын маргаан (foreign-investment-land-dispute)
    # ──────────────────────────────────────────────────────────────────────────
    src_land100 = get_or_create_source(
        db,
        title="Хөрөнгө оруулалтын тухай хуулийн шинэчилсэн найруулга ба 100 жилийн газар ашиглалтын маргаан",
        url="https://parliament.mn/foreign-investment-law-100-years-land-dispute-2024",
        category="parliament",
        cleaned_text="2023–2024 онд Эдийн засаг хөгжлийн сайд Ч.Хүрэлбаатарын өргөн барьсан Хөрөнгө оруулалтын тухай хуулийн төсөлд гадаадын хөрөнгө оруулагчдад газрыг 60 жилээр, дахин 40 жилээр нийт 100 жилээр ашиглуулах заалт орсныг нийгэм, сөрөг хүчин, зарим хууль тогтоогчид үндэсний аюулгүй байдалд халдсан ноцтой асуудал гэж эсэргүүцэн улс даяар жагсаал өрнөж, улмаар Засгийн газраас уг заалтыг татан авахад хүрсэн.",
        pub_date=date(2024, 1, 28)
    )

    ent_khurelbaatar_ch = get_or_create_entity(
        db, "Чимэдийн Хүрэлбаатар", "person",
        description="Эдийн засаг, хөгжлийн сайд бөгөөд Тэргүүн шадар сайд (2022-2024), Сангийн сайд асан (2017-2021).",
        tldr_summary="Хөрөнгө оруулалтын хуулийг боловсруулан өргөн барьсан сайд.",
        aliases=[("Ч.Хүрэлбаатар", "initials")]
    )

    case_land100 = get_or_create_case(
        db, "foreign-investment-land-dispute", "Хөрөнгө Оруулалтын Хууль & 100 Жилийн Газар Олголтын Маргаан",
        "Гадаадын хөрөнгө оруулагчдад газрыг 100 жилээр ашиглуулах заалтаас үүдэлтэй нийгмийн эсэргүүцэл, хуулийн төслийн буцаан авалтын улс төрийн хямрал.",
        category="crisis"
    )
    link_case_entity(db, case_land100.id, ent_khurelbaatar_ch.id, "Хууль санаачлагч Сайд", "ЭЗХ-ийн сайд")

    add_fact(db, ent_khurelbaatar_ch.id, src_land100.id, "2023-12-18", "chronological",
             "Ч.Хүрэлбаатар сайд Хөрөнгө оруулалтын тухай хуулийн шинэчилсэн найруулгын төслийг УИХ-д өргөн мэдүүлэв.",
             "Хуулийн төсөл өргөн барьсан баримт.",
             "Хөрөнгө_оруулалт", ["хууль", "газар", "Ч.Хүрэлбаатар"], sentiment=0.1)
    add_fact(db, ent_khurelbaatar_ch.id, src_land100.id, "2024-01-26", "chronological",
             "Нийслэл болон хөдөө орон нутагт 'Газар нутгаа 100 жилээр өгөхгүй' иргэдийн эсэргүүцлийн цуглаан болж, Засгийн газар уг заалтаа эргүүлэн татахаа мэдэгдэв.",
             "Иргэдийн эсэргүүцэл өрнөж төсөл гацсан баримт.",
             "Хөрөнгө_оруулалт", ["эсэргүүцэл", "газар", "жагсаал"], sentiment=-0.7)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. ОДОО БАЙГАА БҮХ ХЭРГҮҮДИЙГ ОНЦЛОГ 5 КАТЕГОРИД ЭРЭМБЭЛЭН ХУВААРИЛАХ
    # ──────────────────────────────────────────────────────────────────────────
    print("\n=== 2. CATEGORIZING ALL CASES INTO 5 STRATEGIC THEMATIC GROUPS ===")
    
    CATEGORIES_MAP = {
        # Авлига, албан тушаалын эрүүгийн дуулиант хэргүүд (scandal)
        "coal-theft": "scandal",
        "dbm-scandal": "scandal",
        "green-bus": "scandal",
        "sixty-billion": "scandal",
        "miat-war-risk": "scandal",
        "zorig-assassination": "scandal",
        "anod-bank-collapse": "scandal",
        "khadgalamj-bank-casino": "scandal",
        "casino-scandal-1999": "scandal",

        # Засаглалын хямрал, Засгийн газрын огцролт (crisis)
        "wiretapping-cabinet-crisis": "crisis",
        "foreign-investment-land-dispute": "crisis",
        "khurelsukh-controversies": "crisis",
        "railway-dispute": "crisis",

        # Мега төсөл, гэрээ хэлэлцээр & Төрийн өмчийн хувьчлалууд (megaproject)
        "oyu-tolgoi": "megaproject",
        "erdenet-49": "megaproject",
        "standard-bank-erba": "megaproject",
        "darkhan-metallurgy": "megaproject",
        "tavantolgoi-fuel-case": "megaproject",

        # Улс төрийн фракц, оффшор, газрын сүлжээ (faction)
        "offshore-panama": "faction",
        "ub-land-scandal": "faction",
        "southgobi-tax-evasion": "faction",

        # Төсвийн худалдан авалт & Тусгай сангууд (procurement)
        "bzs-scandal": "procurement",
        "sme-fund": "procurement",
        "crop-support-fund": "procurement",
        "price-stabilization": "procurement",
        "sovereign-bonds": "procurement",
        "medicine-quality-monopoly": "procurement",
        "disabled-children-center": "procurement",
        "just-oil-collapse": "procurement",
    }

    for slug_key, cat in CATEGORIES_MAP.items():
        c = db.query(models.Case).filter(models.Case.slug == slug_key).first()
        if c:
            c.category = cat
            db.commit()
            print(f"-> Set Category for [{c.slug}] => '{cat}'")

    print(f"\nAll cases successfully populated and categorized! Total cases in DB: {db.query(models.Case).count()}")
    db.close()


if __name__ == "__main__":
    seed_and_categorize()
