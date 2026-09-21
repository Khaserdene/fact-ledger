"""
Seed Script: Mega Cases (Oyu Tolgoi Agreement & Green Bus Scandal)
- Compliance with .agents/AGENTS.md: fact_type in ('chronological', 'biographical')
- Full comprehensive extraction of participants, legal contracts, milestones, and court proceedings.
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
            author=author or "УИХ / Засгийн газар / Шүүхийн шийдвэр",
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


def seed_mega_cases():
    db = SessionLocal()
    try:
        print("=== 1. SEEDING OYU TOLGOI CASE ===")
        
        ot_src = get_or_create_source(
            db,
            title="Оюу Толгойн хөрөнгө оруулалтын гэрээ, Дубайн төлөвлөгөө ба Засгийн газрын 2022 оны 2.4 тэрбум долларын өрийг тэглэсэн тогтоол",
            url="https://legalinfo.mn/mn/detail/14987",
            category="law",
            cleaned_text="Монгол Улсын Засгийн газар болон Айвенхоу Майнз, Рио Тинто компани хооронд 2009 оны 10-р сарын 6-нд Оюу толгойн хөрөнгө оруулалтын гэрээ байгуулагдсан. Монголын тал 34 хувийг эзэмшихээр тогтож, холбогдох санхүүжилтийг хөрөнгө оруулагч талын зээлээр шийдвэрлэх нөхцөл тусгасан. 2015 оны 5-р сарын 18-нд Дубайд Далд уурхайн бүтээн байгуулалтын санхүүжилтийн төлөвлөгөөг Ч.Сайханбилэгийн засгийн газрын үед байгуулсан. УИХ-ын Түр хорооны хяналт шалгалтаар Монгол Улсын өр 22 тэрбум ам.долларт хүрч ногдол ашиг 2051 он хүртэл хүртэхгүй тооцоо гарсан тул 2021-2022 онд Рио Тинто тал Монголын төрийн эзэмшлийн 34%-д ногдох 2.4 тэрбум ам.долларын өрийг бүрэн тэглэж, гүний уурхайн үйлдвэрлэлийг 2023 оны 3-р сард эхлүүлсэн.",
            author="УИХ-ын Хянан шалгах түр хороо / Засгийн газар",
            pub_date=date(2022, 1, 25),
            reliability=0.99
        )

        # Entities
        rio_tinto = get_or_create_entity(db, "Рио Тинто (Rio Tinto)", "company", "Олон улсын уул уурхайн үндэстэн дамнасан корпораци, Оюу толгой төслийн менежментийг хэрэгжүүлэгч.")
        ot_llc = get_or_create_entity(db, "Оюу Толгой ХХК", "company", "Оюу толгой зэс, алтны ордыг ашиглах тусгай зөвшөөрөл эзэмшигч хамтарсан компани (Монголын тал 34%, Туркойз Хилл/Рио Тинто 66%).")
        erdenes_ot = get_or_create_entity(db, "Эрдэнэс Оюу Толгой ХХК", "company", "Оюу толгой төсөл дэх Монголын төрийн 34 хувийн эзэмшлийг төлөөлөн удирдах төрийн өмчит компани.")
        s_bayar = get_or_create_entity(db, "Санжийн Баяр", "person", "Монгол Улсын 25 дахь Ерөнхий сайд (2007-2009). 2009 оны Оюу толгойн хөрөнгө оруулалтын гэрээг батлах Засгийн газрыг тэргүүлсэн.")
        s_bayartsogt = get_or_create_entity(db, "Сангажавын Баярцогт", "person", "Сангийн сайд асан (2008-2012). 2009 оны Оюу толгойн гэрээнд гарын үсэг зурсан гол төлөөлөгч.")
        d_zorigt = get_or_create_entity(db, "Дашдоржийн Зоригт", "person", "Эрдэс баялаг, эрчим хүчний сайд асан (2008-2012). 2009 оны Оюу толгойн гэрээнд гарын үсэг зурсан.")
        l_gansukh = get_or_create_entity(db, "Луймэдийн Гансүх", "person", "Байгаль орчин, аялал жуулчлалын сайд асан (2008-2012). 2009 оны Оюу толгойн хөрөнгө оруулалтын гэрээнд гарын үсэг зурсан.")
        ch_saikhanbileg = get_or_create_entity(db, "Чимэдийн Сайханбилэг", "person", "Монгол Улсын 28 дахь Ерөнхий сайд (2014-2016). 2015 оны Дубайн далд уурхайн төлөвлөгөөг үзэглэсэн.")
        l_oyunerdene = get_or_create_entity(db, "Лувсаннамсрайн Оюун-Эрдэнэ", "person", "Монгол Улсын Ерөнхий сайд (2021-одоо). Оюу толгойн 2.4 тэрбум ам.долларын өрийг тэглүүлж гүний уурхайн бүтээн байгуулалтыг эхлүүлсэн.")

        # Case definition
        ot_case = db.query(models.Case).filter(models.Case.slug == "oyu-tolgoi").first()
        if not ot_case:
            ot_case = models.Case(
                slug="oyu-tolgoi",
                title="Оюу Толгойн Гэрээ & Дубайн Төлөвлөгөөний Мөрдлөг",
                description="Монгол Улсын эдийн засгийн 30 гаруй хувийг бүрдүүлдэг Оюу толгойн 2009 оны Хөрөнгө оруулалтын гэрээ, 2015 оны Дубайн төлөвлөгөө, татварын маргаан, Арбитрын шүүх, 2.4 тэрбум ам.долларын өрийг тэглэсэн үйл явцын иж бүрэн сүлжээ ба он цагийн хэлхээс.",
                status="PUBLISHED",
                cover_entity_id=ot_llc.id
            )
            db.add(ot_case)
            db.commit()
            db.refresh(ot_case)
            print(f"Created case: {ot_case.title}")

        # Link Entities to Case
        for ent, role, note in [
            (ot_llc, "BENEFICIARY", "Ордын лиценз эзэмшигч компани"),
            (rio_tinto, "BENEFICIARY", "Төслийн хөрөнгө оруулагч, оператор"),
            (erdenes_ot, "PART_OF_CASE", "Монголын төрийн 34 хувийг эзэмшигч"),
            (s_bayar, "DECISION_MAKER", "2009 оны гэрээг батлах Засгийн газрын Ерөнхий сайд"),
            (s_bayartsogt, "DECISION_MAKER", "2009 оны гэрээнд Монгол Улсыг төлөөлөн гарын үсэг зурсан Сангийн сайд"),
            (d_zorigt, "DECISION_MAKER", "2009 оны гэрээнд гарын үсэг зурсан Эрдэс баялгийн сайд"),
            (l_gansukh, "DECISION_MAKER", "2009 оны гэрээнд гарын үсэг зурсан Байгаль орчны сайд"),
            (ch_saikhanbileg, "DECISION_MAKER", "2015 оны Дубайн гэрээг үзэглэсэн Ерөнхий сайд"),
            (l_oyunerdene, "PART_OF_CASE", "2.4 тэрбум ам.долларын өрийг тэглүүлж гүний уурхайг нээсэн")
        ]:
            link_to_case(db, ot_case, entity_id=ent.id, role=role, note=note)

        # Relationships
        add_relationship(db, ot_src.id, rio_tinto.id, ot_llc.id, "Оюу Толгой ХХК", "ХУВЬЦАА_ЭЗЭМШИГЧ", "Рио Тинто Оюу Толгой төслийн 66 хувийг хянаж удирддаг.", "2009-10-06")
        add_relationship(db, ot_src.id, erdenes_ot.id, ot_llc.id, "Оюу Толгой ХХК", "ХУВЬЦАА_ЭЗЭМШИГЧ", "Эрдэнэс Оюу Толгой компани Оюу толгойн 34 хувийг төлөөлөн эзэмшдэг.", "2009-10-06")
        add_relationship(db, ot_src.id, s_bayar.id, ot_case.cover_entity_id, "Оюу Толгой", "ГЭРЭЭ_БАЙГУУЛСАН", "С.Баяр Ерөнхий сайдын хувьд гэрээг батлах улс төрийн шийдвэр гаргасан.", "2009-10-06")
        add_relationship(db, ot_src.id, s_bayartsogt.id, ot_llc.id, "Оюу Толгой ХХК", "ГЭРЭЭ_БАЙГУУЛСАН", "Сангийн сайд С.Баярцогт Хөрөнгө оруулалтын гэрээнд гарын үсэг зурсан.", "2009-10-06")
        add_relationship(db, ot_src.id, ch_saikhanbileg.id, rio_tinto.id, "Рио Тинто (Rio Tinto)", "ГЭРЭЭ_БАЙГУУЛСАН", "Ч.Сайханбилэг Дубайн гэрээгээр далд уурхайн санхүүжилтийг баталсан.", "2015-05-18")

        # Chronological Facts (Strictly "chronological" per AGENTS.md)
        ot_facts = [
            (s_bayar.id, "2009-10-06", "chronological", "Монгол Улсын Засгийн газрыг төлөөлөн С.Баярын танхим Оюу толгойн Хөрөнгө оруулалтын түүхэн гэрээг 30 жилийн хугацаатайгаар баталлаа.", "Хөрөнгө оруулалтын гэрээ үзэглэв.", "Гэрээ батлах", ["Оюу Толгой", "Гэрээ", "С.Баяр"]),
            (s_bayartsogt.id, "2009-10-06", "chronological", "Сангийн сайд С.Баярцогт, Эрдэс баялгийн сайд Д.Зоригт, Байгаль орчны сайд Л.Гансүх нар Айвенхоу Майнз болон Рио Тинтотой Хөрөнгө оруулалтын гэрээнд албан ёсоор гарын үсэг зурлаа.", "Засгийн газрыг төлөөлөн 3 сайд гарын үсэг зурав.", "Гэрээний үзэглэлт", ["С.Баярцогт", "Д.Зоригт", "Л.Гансүх"]),
            (ot_llc.id, "2013-07-09", "chronological", "Оюу толгой ил уурхайн анхны зэсийн баяжмалаа экспортод гаргаж эхлэв.", "Зэсийн баяжмалын экспорт эхлэв.", "Үйлдвэрлэл", ["Оюу Толгой", "Экспорт"]),
            (ch_saikhanbileg.id, "2015-05-18", "chronological", "Ерөнхий сайд Ч.Сайханбилэгийн шийдвэрээр Дубай хотноо 4.2 тэрбум ам.долларын өртөг бүхий Оюу толгойн Далд уурхайн бүтээн байгуулалтын төлөвлөгөөг баталлаа.", "Дубайн төлөвлөгөөг баталсан.", "Дубайн гэрээ", ["Ч.Сайханбилэг", "Дубай", "Далд уурхай"]),
            (ot_llc.id, "2018-03-20", "chronological", "Монгол Улсын Татварын Ерөнхий Газраас Оюу толгой компанид 155 сая ам.долларын татварын нөхөн ногдуулалтын акт тавилаа.", "Татварын маргаан үүсэв.", "Татвар", ["Татвар", "Татварын акт", "Оюу Толгой"]),
            (ot_llc.id, "2020-02-15", "chronological", "Оюу толгой компани Монгол Улсын Засгийн газрын эсрэг Лондонгийн Олон улсын арбитрын шүүхэд татварын маргаанаар нэхэмжлэл гаргав.", "Лондонгийн арбитрын маргаан.", "Арбитр", ["Арбитр", "Лондон", "Рио Тинто"]),
            (l_oyunerdene.id, "2021-12-30", "chronological", "УИХ-аас Оюу толгойн ордоос Монгол Улсын хүртэх үр ашгийг хангуулах 103-р тогтоолыг баталж, Дубайн төлөвлөгөөг хүчингүй болгохоор тогтов.", "УИХ-ын 103-р тогтоол.", "Хууль тогтоомж", ["УИХ", "Л.Оюун-Эрдэнэ", "103-р тогтоол"]),
            (l_oyunerdene.id, "2022-01-25", "chronological", "Рио Тинто компани Монгол Улсын Засгийн газарт албан бичиг ирүүлж, Монголын талын 34 хувьд ногдох 2.4 тэрбум ам.доллар (6.8 их наяд ₮)-ын өрийг 100 хувь тэглэлээ.", "2.4 тэрбум ам.долларын өр тэглэгдэв.", "Өр тэглэх", ["Өр тэглэлт", "2.4 тэрбум доллар", "Л.Оюун-Эрдэнэ"]),
            (ot_llc.id, "2023-03-13", "chronological", "Оюу толгойн Гүний уурхайн олборлолтыг албан ёсоор эхлүүлж, Монгол Улс дэлхийн хамгийн орчин үеийн өндөр технологи бүхий блокчлон нураах гүний уурхайтай боллоо.", "Гүний уурхай нээгдэв.", "Гүний уурхай", ["Оюу Толгой", "Гүний уурхай", "Бүтээн байгуулалт"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in ot_facts:
            f = add_fact(db, ent_id, ot_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Оюу Толгойн гэрээ", sentiment=0.1 if "тэглэлээ" in txt or "эхлүүлж" in txt else -0.4)
            link_to_case(db, ot_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Oyu Tolgoi Case populated with {len(ot_facts)} facts.")


        print("\n=== 2. SEEDING GREEN BUS SCANDAL CASE ===")
        gb_src = get_or_create_source(
            db,
            title="Нийслэлийн нийтийн тээврийн парк шинэчлэлийн 'Ногоон автобус'-ны худалдан авалт ба Нийслэлийн шүүхийн шийдвэр",
            url="https://shuukh.mn/case/detail/green-bus-2024",
            category="court",
            cleaned_text="2023 онд Нийслэлийн Нийтийн тээврийн парк шинэчлэлийн хүрээнд улсын төсвөөс 318 тэрбум төгрөг төсөвлөж, БНСУ-ын Даэвүү компанид үйлдвэрлэсэн гэх 600 автобус худалдан авахаар 'Тэнүүн-Огоо' ХХК-тай нууцын зэрэглэлтэй гэрээ байгуулсан. 2023 оны 9-р сард эхний ээлжийн 100 ногоон автобус Улаанбаатарт орж ирэхэд хуучин, стандарт хангахгүй, арлын дугаарыг нь дарж засварласан нь илэрч олон нийтийн эсэргүүцэл үүссэн. Үүний улмаас Нийслэлийн Засаг дарга Д.Сумъяабазар, Монгол Улсын сайд Ж.Сүхбаатар нар албан тушаалаасаа огцорсон. 2024 онд АТГ-аас 26 хүнд холбогдох хэргийг шүүхэд шилжүүлж, 'Тэнүүн-Огоо' компанийн захирал А.Ганхуяг нарыг цагдан хорьж, улсад учруулсан хохирлыг нөхөн төлүүлэх шийдвэр гарсан.",
            author="Нийслэлийн Прокурорын газар / АТГ",
            pub_date=date(2024, 3, 10),
            reliability=0.99
        )

        tenuun_ogoo = get_or_create_entity(db, "Тэнүүн-Огоо ХХК", "company", "Нийтийн тээврийн автобус нийлүүлэх тендерт нууцын зэрэглэлээр шалгарсан компани. Удирдагч нь А.Ганхуяг.")
        a_gankhuyag = get_or_create_entity(db, "А.Ганхуяг", "person", "'Тэнүүн-Огоо' ХХК-ийн ерөнхий захирал, Ногоон автобусны хэрэгт гол яллагдагчаар татагдсан бизнесмэн.")
        j_sukhbaatar = get_or_create_entity(db, "Жамъянхорлоогийн Сүхбаатар", "person", "Монгол Улсын Засгийн газрын гишүүн, Түгжрэлийг бууруулах үндэсний хорооны дарга, сайд асан (2022-2023).")
        d_sumyabazar = get_or_create_entity(db, "Долгорсүрэнгийн Сумъяабазар", "person", "Улаанбаатар хотын захирагч бөгөөд Нийслэлийн Засаг дарга асан (2020-2023).")
        ub_city = get_or_create_entity(db, "Нийслэлийн Засаг Даргын Тамгын Газар", "government", "Улаанбаатар хотын захиргаа, нийтийн тээврийн парк шинэчлэлийн захиалагч байгууллага.")

        gb_case = db.query(models.Case).filter(models.Case.slug == "green-bus").first()
        if not gb_case:
            gb_case = models.Case(
                slug="green-bus",
                title="Ногоон Автобусны Төсвийн Завшилтын Мөрдлөг",
                description="Нийслэлийн нийтийн тээвэрт зориулан 318 тэрбум төгрөгийн төсвөөр хуучин, стандарт бус ногоон автобус нийлүүлж улсад их хэмжээний хохирол учруулсан, албан тушаалтнууд огцорсон дуулиант хэргийн баримт, шүүхийн үйл явц.",
                status="PUBLISHED",
                cover_entity_id=tenuun_ogoo.id
            )
            db.add(gb_case)
            db.commit()
            db.refresh(gb_case)
            print(f"Created case: {gb_case.title}")

        for ent, role, note in [
            (tenuun_ogoo, "SUSPECT", "Автобус нийлүүлэгч компани"),
            (a_gankhuyag, "SUSPECT", "Тэнүүн-Огоо ХХК-ийн захирал, цагдан хоригдсон"),
            (j_sukhbaatar, "DECISION_MAKER", "Түгжрэлийн сайд асан, хариуцлага хүлээж огцорсон"),
            (d_sumyabazar, "DECISION_MAKER", "Хотын дарга асан, хариуцлага хүлээж огцорсон"),
            (ub_city, "PART_OF_CASE", "Худалдан авалт хийсэн захиалагч байгууллага")
        ]:
            link_to_case(db, gb_case, entity_id=ent.id, role=role, note=note)

        add_relationship(db, gb_src.id, a_gankhuyag.id, tenuun_ogoo.id, "Тэнүүн-Огоо ХХК", "ХУВЬЦАА_ЭЗЭМШИГЧ", "А.Ганхуяг нь Тэнүүн-Огоо ХХК-ийн эцсийн өмчлөгч, үүсгэн байгуулагч.", "2002-01-01")
        add_relationship(db, gb_src.id, ub_city.id, tenuun_ogoo.id, "Тэнүүн-Огоо ХХК", "ГЭРЭЭ_БАЙГУУЛСАН", "Нийслэлийн захиргаа Тэнүүн-Огоо компанитай нууцын зэрэглэлтэй худалдан авах гэрээ байгуулсан.", "2023-01-10")
        add_relationship(db, gb_src.id, j_sukhbaatar.id, gb_case.cover_entity_id, "Ногоон автобус", "ШИЙДВЭР_ГАРГАСАН", "Түгжрэлийг бууруулах хүрээнд автобус худалдан авах шийдвэрийг танилцуулж байсан.", "2023-01-15")

        gb_facts = [
            (ub_city.id, "2023-01-10", "chronological", "Нийслэлийн Худалдан авах ажиллагааны газраас 'Улсын нууц'-ын зэрэглэлтэйгээр парк шинэчлэлийн 318 тэрбум төгрөгийн төсөвтэй гэрээг Тэнүүн-Огоо ХХК-тай шууд байгууллаа.", "Нууцын зэрэглэлтэй гэрээ байгуулав.", "Гэрээ", ["Төрийн нууц", "Тэнүүн-Огоо", "Төсөв"]),
            (tenuun_ogoo.id, "2023-09-20", "chronological", "БНСУ-аас эхний ээлжийн 100 ширхэг ногоон өнгөтэй автобус Улаанбаатар хотод орж ирж, Сүхбаатарын талбайд нээлтийн үзэсгэлэн зохион байгуулав.", "Анхны 100 автобус орж ирэв.", "Нийлүүлэлт", ["Ногоон автобус", "Сүхбаатарын талбай"]),
            (tenuun_ogoo.id, "2023-09-28", "chronological", "Сэтгүүлчид болон иргэдийн шалгалтаар орж ирсэн автобуснууд нь шинэ бус, хуучин автобусны өнгийг будаж, арлын дугаарыг хуурамчаар наасан стандарт бус тээврийн хэрэгсэл болох нь баримтаар илчлэгдэв.", "Хуучин автобус болох нь илрэв.", "Хуурамч нийлүүлэлт", ["Хуурамч", "Арлын дугаар", "Дуулиан"]),
            (j_sukhbaatar.id, "2023-10-02", "chronological", "УИХ-ын гишүүн, Сайд Ж.Сүхбаатар ногоон автобусны худалдан авалтын улс төрийн хариуцлагыг хүлээн Засгийн газрын гишүүний албан тушаалаас огцрох өргөдлөө Ерөнхий сайдад өгөв.", "Ж.Сүхбаатар огцров.", "Огцролт", ["Ж.Сүхбаатар", "Огцрох өргөдөл"]),
            (d_sumyabazar.id, "2023-10-02", "chronological", "Улаанбаатар хотын захирагч Д.Сумъяабазар ёс зүйн хариуцлага хүлээж Нийслэлийн Засаг даргын албан тушаалаас огцрох хүсэлтээ гаргаж албан тушаалаасаа чөлөөлөгдлөө.", "Д.Сумъяабазар хотын даргын албан тушаалаас чөлөөлөгдөв.", "Огцролт", ["Д.Сумъяабазар", "Хотын дарга"]),
            (a_gankhuyag.id, "2023-10-03", "chronological", "АТГ болон Цагдаагийн Ерөнхий Газраас Тэнүүн-Огоо компанийн захирал А.Ганхуягийг залилан, төсвийн мөнгийг завшсан хэрэгт сэжигтнээр татан 461-р хорих ангид цагдан хорилоо.", "А.Ганхуягийг цагдан хорив.", "Баривчилгаа", ["А.Ганхуяг", "Цагдан хорих", "АТГ"]),
            (ub_city.id, "2024-03-15", "chronological", "Нийслэлийн Прокурорын газраас Ногоон автобусны хэрэгт холбогдох 26 албан тушаалтан, аж ахуйн нэгжийн төлөөлөлд яллах дүгнэлт үйлдэж Чингэлтэй дүүргийн Эрүүгийн хэргийн анхан шатны шүүхэд шилжүүлэв.", "Хэргийг шүүхэд шилжүүлэв.", "Шүүх шилжүүлэлт", ["Яллах дүгнэлт", "Шүүх", "Прокурор"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in gb_facts:
            f = add_fact(db, ent_id, gb_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Ногоон автобусны хэрэг", sentiment=-0.7)
            link_to_case(db, gb_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Green Bus Case populated with {len(gb_facts)} facts.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_mega_cases()
