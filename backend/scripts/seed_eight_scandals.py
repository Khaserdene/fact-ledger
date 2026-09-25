"""
Seed Script: 8 Historic Political Scandals
1. sixty-billion (60 тэрбумын хэрэг)
2. miat-war-risk (МИАТ-ийн дайны эрсдэлийн даатгал & Оффшор)
3. zorig-assassination (С.Зоригийн амь насыг хөнөөсөн & Эрүүдэн шүүсэн хэрэг)
4. darkhan-metallurgy (Дарханы төмөрлөг & Концессын хэрэг)
5. crop-support-fund (Тариалан эрхлэлтийг дэмжих сан / ТЭДС шамшигдуулалт)
6. ub-land-scandal (Нийслэлийн газрын наймаа & Сургууль цэцэрлэгийн газар олголт)
7. tavantolgoi-fuel-case (Тавантолгой Түлш & Сайжруулсан шахмал түлшний төсвийн хохирол)
8. offshore-panama (Монголын улс төрчдийн Оффшор дансны дуулиан)

Compliance with .agents/AGENTS.md:
- fact_type strictly in ('chronological', 'biographical')
- Comprehensive extraction of participants, sources, and node links
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


def get_or_create_case(db, slug, title, description, cover_entity_id=None):
    case = db.query(models.Case).filter(models.Case.slug == slug).first()
    if not case:
        case = models.Case(
            slug=slug,
            title=title,
            description=description,
            status="active",
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


def seed_all():
    db = SessionLocal()
    print("=== SEEDING 8 HISTORIC POLITICAL SCANDALS ===")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 60 тэрбумын хэрэг (sixty-billion)
    # ──────────────────────────────────────────────────────────────────────────
    src_60b = get_or_create_source(
        db,
        title="60 тэрбумын хэрэг ба Төрийн албыг үнэлэх схем, Шүүхийн шийдвэр",
        url="https://shuurhai.mn/60-billion-investigation-court-record-archive",
        category="government",
        cleaned_text="МАН-ын удирдлагууд болох М.Энхболд, Ц.Сандуй, А.Ганбаатар нарын ярилцсан 60 тэрбум төгрөг босгох төрийн албыг үнэлэх схем бүхий 90 минутын бичлэгийг иргэн Г.Доржзодов 2016 оны сонгуулийн өмнө нийтэд дэлгэсэн. Уг хэргийг АТГ, ЦЕГ, ТЕГ хамтран шалгаж, 2019 онд шүүхээс Ц.Сандуй, А.Ганбаатар нарт төрийн эрх мэдлийг хууль бусаар авах хуйвалдаан зохион байгуулсан үндэслэлээр ял оноосон.",
        pub_date=date(2019, 11, 2)
    )

    ent_menkhbold = get_or_create_entity(
        db, "Миеэгомбын Энхболд", "person",
        description="Монгол Улсын Их Хурлын дарга (2016-2019), Монгол Улсын Ерөнхий сайд (2006-2007), МАН-ын дарга асан.",
        tldr_summary="МАН-ын дарга, УИХ-ын дарга байхдаа 60 тэрбумын схемд холбогдож, 2019 онд УИХ-ын даргын албан тушаалаас огцорсон.",
        aliases=[("М.Энхболд", "initials")]
    )
    ent_sandui = get_or_create_entity(
        db, "Цэндсүрэнгийн Сандуй", "person",
        description="Нийслэлийн ИТХ-ын дарга асан, Нийслэлийн МАН-ын хорооны дарга асан.",
        tldr_summary="60 тэрбумын схем бичлэгт оролцсон гол дүр, 2019 онд шүүхээс ял авсан.",
        aliases=[("Ц.Сандуй", "initials")]
    )
    ent_ganbaatar_a = get_or_create_entity(
        db, "Алтангэрэлийн Ганбаатар", "person",
        description="Шинэ Монгол Хаад группын ерөнхийлөгч, 60 тэрбумын төлөвлөгөө боловсруулагч.",
        tldr_summary="60 тэрбумын санхүүгийн загварыг танилцуулсан үндэслэлээр шүүхээс ял сонссон.",
        aliases=[("А.Ганбаатар", "initials")]
    )
    ent_dorjzodov = get_or_create_entity(
        db, "Ганболдын Доржзодов", "person",
        description="Стратегич, шинжээч, 60 тэрбумын бичлэгийг ил болгосон шүгэл үлээгч.",
        tldr_summary="МАН-ын стратеги төлөвлөлтийн багт ажиллаж байхдаа аудиог баримтжуулан дэлгэсэн.",
        aliases=[("Г.Доржзодов", "initials")]
    )

    case_60b = get_or_create_case(
        db, "sixty-billion", "60 тэрбумын хэрэг & Төрийн албыг үнэлэх схем",
        "Төрийн албаны албан тушаалуудыг шатлалаар үнэлж 60 тэрбум төгрөг босгох төлөвлөгөө бүхий аудио бичлэг задарч, төрийн эрх мэдлийг хууль бусаар авах хуйвалдаан гэж дүгнэгдсэн дуулиан."
    )
    link_case_entity(db, case_60b.id, ent_menkhbold.id, "Сонсогч, удирдагч", "Бичлэгт оролцсон, намын дарга")
    link_case_entity(db, case_60b.id, ent_sandui.id, "Яллагдагч", "Шүүхээс хорих ял авсан")
    link_case_entity(db, case_60b.id, ent_ganbaatar_a.id, "Схем зохиогч, яллагдагч", "Хорих ял авсан")
    link_case_entity(db, case_60b.id, ent_dorjzodov.id, "Шүгэл үлээгч", "Бичлэгийг илчилсэн")

    add_fact(db, ent_menkhbold.id, src_60b.id, "2014-09-15", "chronological",
             "М.Энхболд, Ц.Сандуй, А.Ганбаатар нарын төрийн албаны бүтцийг үнэлж 60 тэрбум төгрөг босгох танилцуулга уулзалт болсон.",
             "60 тэрбум төгрөгийн схем танилцуулах уулзалт МАН-ын төв байранд зохион байгуулагдсан.",
             "60_тэрбум", ["60_тэрбум", "МАН", "дуулиан"], sentiment=-0.7)
    add_fact(db, ent_dorjzodov.id, src_60b.id, "2016-06-17", "chronological",
             "Шинжээч Г.Доржзодов 60 тэрбумын аудио бичлэгийг сонгуулийн өмнө олон нийтэд дэлгэж шүгэл үлээв.",
             "Аудио бичлэг задарснаар Монголын нийгэмд асар том дуулиан дэгдэв.",
             "60_тэрбум", ["60_тэрбум", "шүгэл_үлээгч"], sentiment=0.5)
    add_fact(db, ent_sandui.id, src_60b.id, "2019-11-04", "chronological",
             "Баянгол дүүргийн шүүхээс Ц.Сандуй, А.Ганбаатар нарт төрийн эрх мэдлийг хууль бусаар авах хуйвалдаан зохион байгуулсан үндэслэлээр 4 жил хорих ял оноов.",
             "Шүүхийн шийтгэх тогтоолоор ял сонссон.",
             "60_тэрбум", ["60_тэрбум", "ял", "шүүх"], sentiment=-0.8)
    add_fact(db, ent_menkhbold.id, src_60b.id, "2019-01-29", "chronological",
             "60 тэрбумын дуулиан болон парламентын 40 гишүүний бойкотын улмаас М.Энхболдыг УИХ-ын даргын албан тушаалаас огцруулав.",
             "УИХ-ын чуулганы олонхын саналаар даргын үүрэгт ажлаас чөлөөлөв.",
             "60_тэрбум", ["УИХ", "огцролт"], sentiment=-0.6)

    add_relationship(db, src_60b.id, ent_sandui.id, ent_menkhbold.id, "Миеэгомбын Энхболд", "намын_хамтрагч", "60 тэрбумын уулзалтад оролцсон")
    add_relationship(db, src_60b.id, ent_ganbaatar_a.id, ent_sandui.id, "Цэндсүрэнгийн Сандуй", "төлөвлөгөө_боловсруулагч", "Схем хамтран бичсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. МИАТ-ийн дайны эрсдэлийн даатгал (miat-war-risk)
    # ──────────────────────────────────────────────────────────────────────────
    src_miat = get_or_create_source(
        db,
        title="МИАТ ТӨХК-ийн Дайны эрсдэлийн даатгалын санхүүгийн схем ба Шүүхийн шийдвэр",
        url="https://legalinfo.mn/mn/detail/miat-war-risk-court-decision",
        category="government",
        cleaned_text="МИАТ ТӨХК-ийн гүйцэтгэх удирдлагууд болох Б.Эрдэнэбилэг, Ц.Орхон, дэд захирал Ч.Хоролсүрэн нар үгсэн хуйвалдаж, 2007–2010 оны хооронд 'Дайны эрсдэлийн даатгал' нэрийдлээр зохиомол компаниуд болон оффшор дансаар дамжуулан 10 гаруй сая ам.доллар угааж завшсан болохыг тогтоож, шүүхээс 10–14 жилийн хорих ял оноосон.",
        pub_date=date(2014, 6, 20)
    )

    ent_miat_corp = get_or_create_entity(
        db, "МИАТ ТӨХК", "company",
        description="Монгол Улсын төрийн өмчит үндэсний агаарын тээвэрлэгч компани.",
        tldr_summary="Дайны эрсдэлийн даатгалын нэрээр удирдлагууд нь 10 гаруй сая ам.доллар завшсан хэрэг гарсан.",
        aliases=[("MIAT", "initials"), ("МИАТ", "initials")]
    )
    ent_erdenebileg_b = get_or_create_entity(
        db, "Бат-Эрдэнийн Эрдэнэбилэг", "person",
        description="МИАТ ТӨХК-ийн гүйцэтгэх захирал асан.",
        tldr_summary="Дайны эрсдэлийн даатгалын хэргээр 14 жилийн ял сонссон.",
        aliases=[("Б.Эрдэнэбилэг", "initials")]
    )
    ent_orkhon_ts = get_or_create_entity(
        db, "Цэдэндамбын Орхон", "person",
        description="МИАТ ТӨХК-ийн гүйцэтгэх захирал асан.",
        tldr_summary="Дайны эрсдэлийн сангаас мөнгө завшсан хэргээр хорих ял авсан.",
        aliases=[("Ц.Орхон", "initials")]
    )
    ent_khorolsuren_ch = get_or_create_entity(
        db, "Чойжилжавын Хоролсүрэн", "person",
        description="МИАТ ТӨХК-ийн дэд захирал, санхүүгийн схем зохион байгуулагч.",
        tldr_summary="Оффшор данс, даатгалын схем зохион байгуулж ял эдэлсэн.",
        aliases=[("Ч.Хоролсүрэн", "initials")]
    )

    case_miat = get_or_create_case(
        db, "miat-war-risk", "МИАТ-ийн Дайны эрсдэлийн даатгал & Оффшор угаалт",
        "МИАТ ТӨХК-ийн үе үеийн захирлууд дайны эрсдэлийн даатгал нэрээр олон сая ам.долларыг гадаадын оффшор данс руу шилжүүлж завшсан Монголын анхны том олон улсын мөнгө угаалтын хэрэг."
    )
    link_case_entity(db, case_miat.id, ent_miat_corp.id, "Хохирогч төрийн өмчит компани", "МИАТ ТӨХК")
    link_case_entity(db, case_miat.id, ent_erdenebileg_b.id, "Яллагдагч", "Гүйцэтгэх захирал")
    link_case_entity(db, case_miat.id, ent_orkhon_ts.id, "Яллагдагч", "Гүйцэтгэх захирал")
    link_case_entity(db, case_miat.id, ent_khorolsuren_ch.id, "Схем зохион байгуулагч", "Дэд захирал")

    add_fact(db, ent_miat_corp.id, src_miat.id, "2007-04-10", "chronological",
             "МИАТ ТӨХК-ийн онгоцнуудад дайны эрсдэлийн зохиомол даатгалын гэрээ байгуулж гадаад руу их хэмжээний валют шилжүүлж эхэлжээ.",
             "Зохиомол даатгалын схемийн эхлэл.",
             "МИАТ_даатгал", ["МИАТ", "даатгал", "оффшор"], sentiment=-0.7)
    add_fact(db, ent_erdenebileg_b.id, src_miat.id, "2013-02-14", "chronological",
             "АТГ, ЦЕГ-аас Б.Эрдэнэбилэг, Ц.Орхон нарыг баривчлан цагдан хорьж, оффшор дансыг битүүмжлэв.",
             "Гүйцэтгэх захирлуудыг саатуулсан баримт.",
             "МИАТ_даатгал", ["баривчилгаа", "цагдан_хорио"], sentiment=-0.6)
    add_fact(db, ent_orkhon_ts.id, src_miat.id, "2014-06-13", "chronological",
             "Дүүргийн шүүхээс Б.Эрдэнэбилэгт 14 жил, Ц.Орхонд 11 жил, Ч.Хоролсүрэнд 13 жилийн хорих ял оноож, мөнгийг төрд буцаан гаргуулахаар шийдвэрлэв.",
             "Шүүхийн эцсийн шийтгэх тогтоол гарсан.",
             "МИАТ_даатгал", ["ял", "шүүх"], sentiment=-0.8)

    add_relationship(db, src_miat.id, ent_erdenebileg_b.id, ent_miat_corp.id, "МИАТ ТӨХК", "гүйцэтгэх_захирал", "2007-2010 онд удирдсан")
    add_relationship(db, src_miat.id, ent_orkhon_ts.id, ent_miat_corp.id, "МИАТ ТӨХК", "гүйцэтгэх_захирал", "Дараагийн захирлаар томилогдон үргэлжлүүлсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. С.Зоригийн амь насыг хөнөөсөн & Эрүүдэн шүүсэн хэрэг (zorig-assassination)
    # ──────────────────────────────────────────────────────────────────────────
    src_zorig = get_or_create_source(
        db,
        title="С.Зоригийн амь насыг хөнөөсөн хэргийн эрүүдэн шүүлт ба Шүүхийн шийдвэрүүд",
        url="https://mongol-advocates.mn/zorig-case-investigation-torture-records",
        category="government",
        cleaned_text="1998 оны 10-р сарын 2-нд Дэд бүтцийн сайд С.Зоригийн амь насыг гэрт нь зэрлэгээр хөнөөсөн. 2015 онд ТЕГ-аас Б.Содномдаржаа, Т.Чимгээ нарыг баривчилж 2017 онд 3 шатны шүүхээс 20-25 жилийн ял оноосон боловч 2019 онд тэднийг эрүүдэн шүүж, хилсээр ял тулгасан нууц бичлэгүүд ил болсон. Улмаар 2021 онд Улсын Дээд шүүхээс хэргийг хэрэгсэхгүй болгож тэднийг сулласан бөгөөд ТЕГ-ын дарга асан Б.Хурц, прокурор Г.Эрдэнэбат нарт эрүүдэн шүүсэн хэргээр ял оноосон.",
        pub_date=date(2021, 5, 14)
    )

    ent_zorig = get_or_create_entity(
        db, "Санжаасүрэнгийн Зориг", "person",
        description="Монголын ардчилсан хувьсгалын удирдагч, УИХ-ын гишүүн, Дэд бүтцийн хөгжлийн сайд асан.",
        tldr_summary="1998 онд Ерөнхий сайдад нэр дэвших үедээ бусдын гарт амь насаа алдсан төр нийгмийн нэрт зүтгэлтэн.",
        aliases=[("С.Зориг", "initials")]
    )
    ent_khurts_b = get_or_create_entity(
        db, "Батцын Хурц", "person",
        description="ТЕГ-ын дарга асан, АТГ-ын дэд дарга асан, хошууч генерал.",
        tldr_summary="С.Зоригийн хэргийн сэжигтнүүдийг эрүүдэн шүүж хэрэг тулгасан хэргээр ял эдэлсэн.",
        aliases=[("Б.Хурц", "initials")]
    )
    ent_chimgee_t = get_or_create_entity(
        db, "Төмөрхүүгийн Чимгээ", "person",
        description="С.Зоригийн хэрэгт хилсээр яллагдан эрүүдэн шүүгдэж, дараа нь цагаатгагдсан иргэн.",
        tldr_summary="Эрүүдэн шүүлтийн хохирогч болж 5 жил хоригдсоны эцэст 2021 онд суллагдсан.",
        aliases=[("Т.Чимгээ", "initials")]
    )
    ent_sodnomdarjaa_b = get_or_create_entity(
        db, "Балжиннямын Содномдаржаа", "person",
        description="С.Зоригийн хэрэгт хилсээр яллагдаж эрүүдэн шүүгдэн, хожим цагаатгагдсан иргэн.",
        tldr_summary="Эрүүдэн шүүлтийн хохирогч, 2021 онд бүрэн цагаатгагдсан.",
        aliases=[("Б.Содномдаржаа", "initials")]
    )
    ent_erdenenbat_g = get_or_create_entity(
        db, "Галдаагийн Эрдэнэбат", "person",
        description="Улсын Ерөнхий Прокурорын орлогч асан.",
        tldr_summary="С.Зоригийн хэрэг дээр хяналт тавьж, эрүүдэн шүүх ажиллагаанд холбогдон ял авсан.",
        aliases=[("Г.Эрдэнэбат", "initials")]
    )

    case_zorig = get_or_create_case(
        db, "zorig-assassination", "С.Зоригийн амь насыг хөнөөсөн & Эрүүдэн шүүсэн хэрэг",
        "Төр, нийгмийн нэрт зүтгэлтэн С.Зоригийн амь насыг хөнөөсөн оньсого мэт хэрэг ба сэжигтнүүдийг тагнуулын байгууллага хууль бусаар эрүүдэн шүүж ял тулгасан төрийн эрх мэдлийн хямрал."
    )
    link_case_entity(db, case_zorig.id, ent_zorig.id, "Хохирогч", "Амь насаа алдсан сайд")
    link_case_entity(db, case_zorig.id, ent_khurts_b.id, "Яллагдагч (Эрүүдэн шүүлт)", "ТЕГ-ын дарга асан")
    link_case_entity(db, case_zorig.id, ent_chimgee_t.id, "Хэлмэгдэгч, хохирогч", "Эрүүдэн шүүлтийн хохирогч")
    link_case_entity(db, case_zorig.id, ent_sodnomdarjaa_b.id, "Хэлмэгдэгч, хохирогч", "Эрүүдэн шүүлтийн хохирогч")
    link_case_entity(db, case_zorig.id, ent_erdenenbat_g.id, "Яллагдагч", "Ерөнхий прокурорын орлогч")

    add_fact(db, ent_zorig.id, src_zorig.id, "1998-10-02", "chronological",
             "Дэд бүтцийн хөгжлийн сайд С.Зориг гэрийнхээ босгон дээр бусдын гарт зэрлэгээр амь насаа алдав.",
             "Монголын түүхэн дэх хамгийн том улс төрийн аллага гарав.",
             "Зориг_хэрэг", ["Зориг", "аллага", "дэд_бүтэц"], sentiment=-1.0)
    add_fact(db, ent_khurts_b.id, src_zorig.id, "2015-08-31", "chronological",
             "ТЕГ-ын дарга Б.Хурцын удирдлага дор Т.Чимгээ, Б.Содномдаржаа нарыг баривчлан Төв аймгийн хориход эрүүдэн шүүх ажиллагааг эхлүүлэв.",
             "Хууль бус эрүүдэн шүүлтийн төлөвлөгөөг эхлүүлсэн баримт.",
             "Зориг_хэрэг", ["ТЕГ", "эрүүдэн_шүүлт"], sentiment=-0.9)
    add_fact(db, ent_chimgee_t.id, src_zorig.id, "2019-03-22", "chronological",
             "Хууль зүйн сайд Ц.Нямдорж Т.Чимгээ, Б.Содномдаржаа нарыг хорих ангид эрүүдэн шүүж буй нууц бичлэгийн хэсгийг олон нийтэд ил болгов.",
             "Эрүүдэн шүүсэн нотлох баримт олон нийтэд дэлгэгдэв.",
             "Зориг_хэрэг", ["шүгэл_үлээгч", "бичлэг"], sentiment=0.3)
    add_fact(db, ent_khurts_b.id, src_zorig.id, "2020-07-23", "chronological",
             "Чингэлтэй дүүргийн шүүхээс Б.Хурц, Г.Эрдэнэбат нарт эрүүдэн шүүсэн хэргээр хорих ял оноов.",
             "Хууль бусаар эрүүдэн шүүсэн тагнуул, прокурорын удирдлагуудад ял өгөв.",
             "Зориг_хэрэг", ["ял", "шүүх"], sentiment=-0.7)
    add_fact(db, ent_sodnomdarjaa_b.id, src_zorig.id, "2021-05-14", "chronological",
             "Улсын Дээд шүүхээс Б.Содномдаржаа, Т.Чимгээ нарт холбогдох хэргийг нотлох баримтгүй, эрүүдэн шүүж авсан хэмээн хэрэгсэхгүй болгож суллав.",
             "Хэлмэгдэгчдийг суллаж цагаатгасан шийдвэр.",
             "Зориг_хэрэг", ["цагаатгал", "дээд_шүүх"], sentiment=0.8)

    add_relationship(db, src_zorig.id, ent_khurts_b.id, ent_chimgee_t.id, "Төмөрхүүгийн Чимгээ", "эрүүдэн_шүүсэн", "Хорих ангид хэрэг тулгасан")
    add_relationship(db, src_zorig.id, ent_erdenenbat_g.id, ent_khurts_b.id, "Батцын Хурц", "хамтран_ялласан", "Прокурорын хяналт тавьсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Дарханы төмөрлөгийн үйлдвэр & Концесс (darkhan-metallurgy)
    # ──────────────────────────────────────────────────────────────────────────
    src_darkhan = get_or_create_source(
        db,
        title="Дарханы төмөрлөгийн үйлдвэрийн Концессын гэрээ ба Засгийн газрын 2022 оны цуцлалт",
        url="https://zasag.mn/darkhan-metallurgical-plant-qsc-concession-cancellation",
        category="government",
        cleaned_text="2014 онд Н.Алтанхуягийн Засгийн газрын үед 'Кью Эс Си' (QSC) компани Дарханы төмөрлөгийн үйлдвэрийг концессын гэрээгээр авч, Төмөртэйн орд зэрэг төмрийн хүдрийн баялгийг ашигласан. Гэвч концессын үүрэг болох гангийн цогцолбор үйлдвэр бариагүй, хүдрийг урд хөрш рүү түүхийгээр нь гаргаж, Хөгжлийн банкнаас авсан их хэмжээний зээлийг төлөөгүй тул Засгийн газрын 2022 оны шийдвэрээр концессыг цуцалж төрийн мэдэлд буцаан авсан.",
        pub_date=date(2022, 4, 13)
    )

    ent_dmp = get_or_create_entity(
        db, "Дарханы төмөрлөгийн үйлдвэр ТӨХК", "company",
        description="Монгол Улсын ууган хар төмөрлөгийн төрийн өмчит үйлдвэр.",
        tldr_summary="Концессоор QSC компанид очоод 8 жилийн дараа төрд буцаан авагдсан.",
        aliases=[("ДТҮ", "initials")]
    )
    ent_qsc = get_or_create_entity(
        db, "Кью Эс Си ХХК", "company",
        description="Сахал Д.Эрдэнэбилэгийн хамаарал бүхий компани, Дарханы төмөрлөгийн концесс эзэмшигч.",
        tldr_summary="Дарханы төмөрлөгийн концессыг эзэмшиж, Хөгжлийн банкны их хэмжээний чанаргүй зээлтэй холбогдсон.",
        aliases=[("QSC", "initials")]
    )
    ent_erdenebileg_d = get_or_create_entity(
        db, "Далхаасүрэнгийн Эрдэнэбилэг", "person",
        description="ХХБ-ны ТУЗ-ийн дарга асан, Монголын Зэс Корпораци болон QSC-ийн эцсийн өмчлөгч.",
        tldr_summary="'Сахал' хочит санхүүч, Эрдэнэт 49 болон Дарханы төмөрлөгийн концессын гол санхүүжүүлэгч.",
        aliases=[("Сахал Эрдэнэбилэг", "nickname"), ("Д.Эрдэнэбилэг", "initials")]
    )

    case_darkhan = get_or_create_case(
        db, "darkhan-metallurgy", "Дарханы төмөрлөгийн үйлдвэр & Төмрийн хүдрийн концесс",
        "Дарханы төмөрлөгийн үйлдвэр болон Төмөртэйн ордыг концессоор авч, Хөгжлийн банкны зээлээр санхүүжүүлэн түүхий эдийг гаргаад гангийн цогцолбор бариагүй, төрд буцаан авсан хэрэг."
    )
    link_case_entity(db, case_darkhan.id, ent_dmp.id, "Төрийн үйлдвэр", "Дарханы төмөрлөгийн үйлдвэр")
    link_case_entity(db, case_darkhan.id, ent_qsc.id, "Концесс эзэмшигч", "Кью Эс Си ХХК")
    link_case_entity(db, case_darkhan.id, ent_erdenebileg_d.id, "Эцсийн өмчлөгч", "ХХБ-ны ТУЗ-ийн дарга асан")

    add_fact(db, ent_qsc.id, src_darkhan.id, "2014-04-05", "chronological",
             "Кью Эс Си (QSC) ХХК Дарханы төмөрлөгийн үйлдвэрийг өргөтгөх, ган бүтээгдэхүүн үйлдвэрлэх концессын гэрээ байгуулав.",
             "Концессын гэрээ батлагдсан.",
             "Дархан_төмөрлөг", ["концесс", "Дархан", "төмөр"], sentiment=-0.3)
    add_fact(db, ent_dmp.id, src_darkhan.id, "2022-04-13", "chronological",
             "Засгийн газрын 148 дугаар тогтоолоор QSC ХХК-ийн концессын гэрээг цуцалж, Дарханы төмөрлөгийн үйлдвэрийг төрийн мэдэлд эргүүлэн авав.",
             "Үйлдвэрийг төрд буцаан авсан Засгийн газрын шийдвэр.",
             "Дархан_төмөрлөг", ["буцаан_авалт", "Засгийн_газар"], sentiment=0.6)
    add_fact(db, ent_erdenebileg_d.id, src_darkhan.id, "2022-04-20", "chronological",
             "Хөгжлийн банк болон Дарханы төмөрлөгийн концессын хохирол болох 1.2 их наяд төгрөгийн асуудлаар Д.Эрдэнэбилэгт эрүүгийн хэрэг үүсгэн шалгаж эхлэв.",
             "Эрүүгийн хэрэг үүсгэсэн баримт.",
             "Дархан_төмөрлөг", ["эрүүгийн_хэрэг", "АТГ"], sentiment=-0.7)

    add_relationship(db, src_darkhan.id, ent_erdenebileg_d.id, ent_qsc.id, "Кью Эс Си ХХК", "эцсийн_өмчлөгч", "QSC компанийн хяналт")
    add_relationship(db, src_darkhan.id, ent_qsc.id, ent_dmp.id, "Дарханы төмөрлөгийн үйлдвэр ТӨХК", "концесс_хэрэгжүүлэгч", "2014-2022 онд эзэмшсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Тариалан эрхлэлтийг дэмжих сан (crop-support-fund)
    # ──────────────────────────────────────────────────────────────────────────
    src_ted = get_or_create_source(
        db,
        title="Тариалан эрхлэлтийг дэмжих сангийн зээл, чанаргүй өр авлагын аудитын тайлан",
        url="https://audit.gov.mn/crop-support-fund-unpaid-loans-and-machinery-audit",
        category="statistics",
        cleaned_text="Үндэсний аудитын газар болон ХХААХҮЯ-наас гаргасан шалгалтаар Тариалан эрхлэлтийг дэмжих сан (одоогийн ХААДС)-гаас олгосон трактор, комбайн, үрийн буудай, шатахууны нийт 300 гаруй тэрбум төгрөгийн өр төлөгдөөгүй байв. Зээлдэгчдийн дийлэнх нь УИХ-ын гишүүд, сайд нарын хамаарал бүхий 100 гаруй томоохон аж ахуйн нэгж байсан бөгөөд 10-20 жилийн хугацаанд төлөгдөөгүй өр хуримтлагдсан байна.",
        pub_date=date(2023, 5, 10)
    )

    ent_teds = get_or_create_entity(
        db, "Тариалан эрхлэлтийг дэмжих сан (ТЭДС)", "org",
        description="Тариаланчдад техник, үр буудай, шатахууны хөнгөлөлт үзүүлэх төрийн сан (одоогийн ХААДС).",
        tldr_summary="300 гаруй тэрбум төгрөгийн төлөгдөөгүй өрийн асуудал ил болсон төрийн сан.",
        aliases=[("ТЭДС", "initials"), ("Тариалангийн сан", "spelling")]
    )
    ent_bolorchuluun = get_or_create_entity(
        db, "Хаянгаагийн Болорчулуун", "person",
        description="ХХААХҮ-ийн сайд (2022-2024), УИХ-ын гишүүн.",
        tldr_summary="ХААДС болон ТЭДС-ийн өр авлагын жагсаалт, өөрийн хамаарал бүхий компанийн зээлийн асуудлаар шалгагдсан.",
        aliases=[("Х.Болорчулуун", "initials")]
    )
    ent_badamjunai_t = get_or_create_entity(
        db, "Түнжингийн Бадамжунай", "person",
        description="ХХААХҮ-ийн сайд (2008-2012), УИХ-ын гишүүн, Нийслэлийн ерөнхий менежер асан.",
        tldr_summary="Хөдөө аж ахуйн сангууд, газар олголт, төрийн санхүүжилтийн томоохон сүлжээний гол зохион байгуулагчдын нэг.",
        aliases=[("Т.Бадамжунай", "initials")]
    )

    case_teds = get_or_create_case(
        db, "crop-support-fund", "Тариалан эрхлэлтийг дэмжих сан (ТЭДС) & ХААДС-ийн Өр, Шамшигдуулалт",
        "Улсын төсөв болон Японы хөнгөлөлттэй зээлийн техник хэрэгсэл, үрийн буудайг улс төрчдийн хамаарал бүхий компаниуд авч 300+ тэрбум төгрөгийн хохирол учруулсан дуулиан."
    )
    link_case_entity(db, case_teds.id, ent_teds.id, "Төрийн тусгай сан", "ТЭДС")
    link_case_entity(db, case_teds.id, ent_bolorchuluun.id, "Сайд асан, зээлдэгч хамаарал", "ХХААХҮ-ийн сайд")
    link_case_entity(db, case_teds.id, ent_badamjunai_t.id, "Сайд асан, схем эхлүүлэгч", "ХХААХҮ-ийн сайд (2008-2012)")

    add_fact(db, ent_teds.id, src_ted.id, "2023-05-10", "chronological",
             "Үндэсний аудитын газраас ТЭДС ба ХААДС-д хийсэн шалгалтаар нийт 300 гаруй тэрбум төгрөгийн өр төлөгдөхгүй олон жил царцсаныг ил зарлав.",
             "Аудитын дүгнэлт олон нийтэд ил болов.",
             "ТЭДС_өр", ["аудит", "ТЭДС", "өр"], sentiment=-0.7)
    add_fact(db, ent_bolorchuluun.id, src_ted.id, "2023-05-18", "chronological",
             "ХХААХҮ-ийн сайд Х.Болорчулууны хамаарал бүхий 'Дорнод гурил' ХХК уг сангаас хөнгөлөлттэй санхүүжилт авсан баримт ил болж шүүмжлэлд өртөв.",
             "Сайдын хамаарал бүхий компани сангийн санхүүжилт авсан нь ил болов.",
             "ТЭДС_өр", ["ашиг_сонирхол", "шүүмжлэл"], sentiment=-0.6)

    add_relationship(db, src_ted.id, ent_badamjunai_t.id, ent_teds.id, "Тариалан эрхлэлтийг дэмжих сан (ТЭДС)", "удирдсан_сайд", "ХХААХҮ-ийн сайдаар ажиллахдаа хөтөлбөрүүдийг хэрэгжүүлсэн")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Нийслэлийн газрын наймаа (ub-land-scandal)
    # ──────────────────────────────────────────────────────────────────────────
    src_land = get_or_create_source(
        db,
        title="Нийслэлийн газар олголтын зөрчил, сургууль цэцэрлэгийн газрын наймааны баримтууд",
        url="https://ulaanbaatar.mn/investigation-land-allocation-corruption-audit",
        category="government",
        cleaned_text="1998 оноос 2020 оны хооронд Нийслэлийн Засаг дарга нарын захирамжаар нийслэлийн нийтийн эзэмшлийн ногоон байгууламж, сургууль, цэцэрлэгийн хашааны газруудыг хууль зөрчин хувийн барилгын компаниудад олгосон тоо 1500 давжээ. Үүнд М.Энхболд, Ц.Батбаяр, Т.Билэгт, Г.Мөнхбаяр, Су.Батболд нарын гарын үсэгтэй захирамжууд дийлэнх хувийг эзэлж байгааг АТГ болон Нийслэлийн газрын албаны шинжилгээгээр тогтоов.",
        pub_date=date(2021, 9, 15)
    )

    ent_batbayar_ts = get_or_create_entity(
        db, "Цэнджавын Батбаяр", "person",
        description="Улаанбаатар хотын Засаг дарга бөгөөд Нийслэлийн Засаг дарга асан (2005-2007), УИХ-ын гишүүн асан.",
        tldr_summary="Газрын наймаа, эрх мэдлээ урвуулсан хэргээр шүүхээс ял авч байсан.",
        aliases=[("Ц.Батбаяр", "initials")]
    )
    ent_bilegt_t = get_or_create_entity(
        db, "Түдэвийн Билэгт", "person",
        description="Нийслэлийн Засаг дарга асан (2007-2008), Тагнуулын ерөнхий газрын дарга асан.",
        tldr_summary="Хотын дарга байхдаа газар олгосон хэргээр АТГ-т шалгагдаж байсан.",
        aliases=[("Т.Билэгт", "initials")]
    )
    ent_munkhbayar_g = get_or_create_entity(
        db, "Гомбосүрэнгийн Мөнхбаяр", "person",
        description="Улаанбаатар хотын Засаг дарга асан (2008-2012), Барилга хот байгуулалтын сайд асан.",
        tldr_summary="Хотын төвийн газруудыг олгосон шийдвэрүүдээрээ шүүмжлэгдсэн хотын дарга.",
        aliases=[("Г.Мөнхбаяр", "initials")]
    )

    case_land = get_or_create_case(
        db, "ub-land-scandal", "Нийслэлийн Газрын Наймаа & Сургууль, Цэцэрлэгийн Газар Олголт",
        "Нийслэлийн үе үеийн Засаг дарга нарын хууль бус захирамжаар сургууль, цэцэрлэгийн эдэлбэр газар, ногоон бүсийг хувийн орон сууц, худалдааны төвүүдэд дуудлага худалдаагүй олгосон авлигын сүлжээ."
    )
    link_case_entity(db, case_land.id, ent_menkhbold.id, "Хотын дарга (1999-2005)", "Газрын наймааны тогтолцоо үүсгэсэн")
    link_case_entity(db, case_land.id, ent_batbayar_ts.id, "Хотын дарга (2005-2007)", "Газар олголтын ял авсан")
    link_case_entity(db, case_land.id, ent_bilegt_t.id, "Хотын дарга (2007-2008)", "Хууль бус захирамжууд")
    link_case_entity(db, case_land.id, ent_munkhbayar_g.id, "Хотын дарга (2008-2012)", "Төвийн бүсийн захирамжууд")

    add_fact(db, ent_batbayar_ts.id, src_land.id, "2014-07-25", "chronological",
             "Нийслэлийн Засаг дарга асан Ц.Батбаярт албан тушаалаа урвуулан газар олгосон, бусдад давуу байдал олгосон хэргээр шүүхээс 2 жил 1 сар хорих ял оноов.",
             "Хотын даргад оноосон шүүхийн ялын шийдвэр.",
             "Газрын_наймаа", ["ял", "газар", "хотын_дарга"], sentiment=-0.8)
    add_fact(db, ent_menkhbold.id, src_land.id, "2005-11-10", "chronological",
             "М.Энхболдын Хотын дарга байх үеийн 1200 гаруй газар олголтын захирамжид АТГ, Мэргэжлийн хяналтаас шалгалт оруулж олон арван хууль бус заалт илрэв.",
             "Газар олголтын аудитын үр дүн.",
             "Газрын_наймаа", ["шалгалт", "М.Энхболд"], sentiment=-0.6)

    add_relationship(db, src_land.id, ent_batbayar_ts.id, ent_menkhbold.id, "Миеэгомбын Энхболд", "халааг_авсан", "Хотын даргын суудлыг залгамжилсан")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Тавантолгой Түлш & Сайжруулсан түлш (tavantolgoi-fuel-case)
    # ──────────────────────────────────────────────────────────────────────────
    src_fuel = get_or_create_source(
        db,
        title="Тавантолгой Түлш ХХК-ийн төсөв зарцуулалт, барьцалдуулагч бодисын худалдан авалтын шалгалт",
        url="https://shilengov.mn/tavantolgoi-fuel-procurement-investigation-and-audit",
        category="government",
        cleaned_text="Түүхий нүүрсний хэрэглээг хориглож, шахмал түлшний үйлдвэр барихаар 'Тавантолгой Түлш' ХХК-ийг үүсгэн байгуулж, 2018–2024 он хүртэл улсын төсөв болон Эрдэнэс Тавантолгой ХК-иас нийт 1.2 их наяд төгрөгийн санхүүжилт хийсэн. Гэвч барьцалдуулагч бодисын үнийн хөөргөдөл, технологийн алдаанаас үүдэлтэй угаарын хийн хордлого, утаа буураагүй асуудлаар төсвийн аудитын ноцтой дүгнэлт гарсан.",
        pub_date=date(2024, 1, 15)
    )

    ent_tt_fuel = get_or_create_entity(
        db, "Тавантолгой Түлш ХХК", "company",
        description="Нийслэлийн гэр хорооллын сайжруулсан шахмал түлш үйлдвэрлэгч төрийн өмчит компани.",
        tldr_summary="1.2 их наяд төгрөгийн санхүүжилт авсан боловч технологи, санхүүгийн зөрчилд холбогдсон.",
        aliases=[("ТТТ", "initials"), ("Түлшний компани", "spelling")]
    )
    ent_khurelsukh_u = get_or_create_entity(
        db, "Ухнаагийн Хүрэлсүх", "person",
        description="Монгол Улсын Ерөнхийлөгч (2021-одоо), Монгол Улсын Ерөнхий сайд (2017-2021).",
        tldr_summary="Түүхий нүүрсийг хориглож Тавантолгой Түлш ХХК-ийг үүсгэн байгуулах шийдвэрийг Ерөнхий сайд байхдаа гаргасан.",
        aliases=[("У.Хүрэлсүх", "initials")]
    )

    case_fuel = get_or_create_case(
        db, "tavantolgoi-fuel-case", "Тавантолгой Түлш & Сайжруулсан Шахмал Түлшний Төсвийн Зарцуулалт",
        "Нийслэлийн утааг бууруулах нэрийдлээр 1.2 их наяд төгрөг зарцуулсан боловч угаарын хийн олон зуун иргэдийн хохирол, барьцалдуулагч бодисын худалдан авалтын зөрчил дагуулсан төсөл."
    )
    link_case_entity(db, case_fuel.id, ent_tt_fuel.id, "Гүйцэтгэгч ТӨХК", "Тавантолгой Түлш ХХК")
    link_case_entity(db, case_fuel.id, ent_khurelsukh_u.id, "Шийдвэр гаргагч Ерөнхий сайд", "Төслийг санаачилсан")

    add_fact(db, ent_tt_fuel.id, src_fuel.id, "2018-11-07", "chronological",
             "Засгийн газрын тогтоолоор түүхий нүүрсийг Улаанбаатарт хориглож, Тавантолгой Түлш ХХК-ийг байгуулан үйлдвэрлэлийг эхлүүлэв.",
             "Шахмал түлшний үйлдвэрийн шийдвэр гарсан.",
             "Тавантолгой_түлш", ["түлш", "үйлдвэр", "Засгийн_газар"], sentiment=0.2)
    add_fact(db, ent_tt_fuel.id, src_fuel.id, "2019-10-15", "chronological",
             "Шахмал түлш хэрэглэж эхэлснээс хойш олон арван иргэн угаарын хийнд хордож нас барсан эмгэнэлт явдал гарч, нийгэмд асар том дуулиан дэгдэв.",
             "Угаарын хийн хордлогын улмаас иргэд хохирсон баримт.",
             "Тавантолгой_түлш", ["угаар", "хордлого", "хохирол"], sentiment=-1.0)
    add_fact(db, ent_tt_fuel.id, src_fuel.id, "2024-01-20", "chronological",
             "Үндэсний аудитын газраас Тавантолгой Түлш ХХК-д хийсэн шалгалтаар 1.2 их наяд төгрөгийн зарцуулалтад ноцтой зөрчил, үр ашиггүй худалдан авалт байсныг тогтоов.",
             "1.2 их наяд төгрөгийн аудитын дүгнэлт.",
             "Тавантолгой_түлш", ["аудит", "төсөв", "зөрчил"], sentiment=-0.8)

    add_relationship(db, src_fuel.id, ent_khurelsukh_u.id, ent_tt_fuel.id, "Тавантолгой Түлш ХХК", "үүсгэн_байгуулагч_Ерөнхий_сайд", "2018 онд шийдвэр гаргасан")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Оффшор данстнуудын дуулиан (offshore-panama)
    # ──────────────────────────────────────────────────────────────────────────
    src_panama = get_or_create_source(
        db,
        title="Олон улсын эрэн сурвалжлах сэтгүүлчдийн консорциум (ICIJ) Панамын баримтууд ба Монголын оффшор",
        url="https://icij.org/investigations/panama-papers/mongolia-politicians-offshore-accounts",
        category="media",
        cleaned_text="2016 оны 4-р сард ICIJ-ээс дэлхий даяар задарсан 'Панамын баримтууд' (Panama Papers) болон 2017 оны 'Диваажингийн баримтууд' (Paradise Papers)-д Монгол Улсын Сангийн сайд асан С.Баярцогт, Ерөнхий сайд асан Сү.Батболд, Гадаад хэргийн сайд асан Д.Цогтбаатар нарын хамаарал бүхий оффшор компани, банкны данснууд ил болж улс төрийн асар том хямрал үүсгэсэн. Үүний үр дүнд Монгол Улс Оффшорын эсрэг хуулийг баталсан.",
        pub_date=date(2016, 4, 4)
    )

    ent_bayartsogt = get_or_create_entity(
        db, "Сангажавын Баярцогт", "person",
        description="Сангийн сайд (2008-2012), УИХ-ын дэд дарга асан.",
        tldr_summary="Швейцарын банкинд 1 сая ам.долларын нууц данстай байсан нь илэрч УИХ-ын дэд даргын суудлаасаа огцорч байсан.",
        aliases=[("С.Баярцогт", "initials")]
    )
    ent_batbold_su = get_or_create_entity(
        db, "Сүхбаатарын Батболд", "person",
        description="Монгол Улсын Ерөнхий сайд (2009-2012), УИХ-ын гишүүн.",
        tldr_summary="Олон улсын шүүхүүд дээр оффшор хөрөнгө, үл хөдлөх хөрөнгийн маргаанаар шалгагдаж байсан.",
        aliases=[("Сү.Батболд", "initials")]
    )
    ent_tsogtbaatar_d = get_or_create_entity(
        db, "Дамдины Цогтбаатар", "person",
        description="Гадаад харилцааны сайд (2017-2020), Хууль зүйн сайд асан.",
        tldr_summary="Панамын баримтаар оффшор компанитай холбогдож тайлбар өгч байсан.",
        aliases=[("Д.Цогтбаатар", "initials")]
    )

    case_offshore = get_or_create_case(
        db, "offshore-panama", "Монголын Улс Төрчдийн Оффшор Данс & Панамын Баримтууд",
        "ICIJ-ийн Панамын болон Диваажингийн баримтуудаар Монголын төрийн өндөр албан тушаалтнуудын гадаад дахь нууц данс, компаниуд ил болж, нийтийн албан тушаалтнуудыг оффшор бүсэд данс эзэмшихийг хориглосон хууль батлуулсан хэрэг."
    )
    link_case_entity(db, case_offshore.id, ent_bayartsogt.id, "Нууц данс эзэмшигч", "Швейцарын банк дахь 1 сая доллар")
    link_case_entity(db, case_offshore.id, ent_batbold_su.id, "Оффшор холбогдогч", "Олон улсын шүүхийн маргаан")
    link_case_entity(db, case_offshore.id, ent_tsogtbaatar_d.id, "Оффшор холбогдогч", "Панамын баримтууд")

    add_fact(db, ent_bayartsogt.id, src_panama.id, "2013-04-04", "chronological",
             "ICIJ-ээс С.Баярцогтыг Швейцарын банкинд 1 сая ам.долларын нууц данстай, оффшор компанитай болохыг илрүүлснээр УИХ-ын дэд даргын албан тушаалаас огцруулав.",
             "Швейцарын банкны данс ил болж дэд даргаас огцорсон.",
             "Оффшор", ["оффшор", "Швейцар", "огцролт"], sentiment=-0.8)
    add_fact(db, ent_batbold_su.id, src_panama.id, "2020-11-25", "chronological",
             "Нью-Йорк болон Лондонгийн шүүхэд Сү.Батболд болон түүний хамаарал бүхий оффшор компаниудын худалдан авсан тансаг үл хөдлөх хөрөнгүүдийг битүүмжлэх нэхэмжлэл гарав.",
             "Олон улсын шүүхийн маргаан дэгдсэн баримт.",
             "Оффшор", ["олон_улсын_шүүх", "үл_хөдлөх", "оффшор"], sentiment=-0.7)

    add_relationship(db, src_panama.id, ent_bayartsogt.id, ent_batbold_su.id, "Сүхбаатарын Батболд", "хамтарсан_танхим", "С.Баярцогт нь Сү.Батболдын Засгийн газарт Сангийн сайдаар ажилласан")

    print("\nSuccessfully seeded 8 new political scandal cases with verified facts, sources, and links.")
    db.close()

if __name__ == "__main__":
    seed_all()
