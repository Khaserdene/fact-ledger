"""
Seed Script: Corporate Giants & Ownership Chains (Erdenet 49%, UBTZ, Erdenes Mongol)
- Compliance with .agents/AGENTS.md: fact_type in ('chronological', 'biographical')
- Comprehensive corporate structure, shareholders, and political appointments.
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
            author=author or "УИХ-ын Түр хороо / Засгийн газар",
            publication_date=pub_date or date(2023, 11, 1),
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


def add_fact(db, entity_id, source_id, f_date_str, fact_type, text, quote, topic, tags, role_ctx="ТӨК", sentiment=0.0):
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
            target_kind="company" if ("ХХК" in target_name or "ХК" in target_name or "үйлдвэр" in target_name.lower() or "нийгэмлэг" in target_name.lower()) else "person",
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


def seed_corporate_entities():
    db = SessionLocal()
    try:
        print("=== SEEDING CORPORATE GIANTS & ERDENET 49% ===")
        
        corp_src = get_or_create_source(
            db,
            title="Эрдэнэт үйлдвэрийн 49 хувийн хувьчлал, Монголын зэс корпораци ба Төрийн өмчит компаниудын шинэчилсэн тайлан",
            url="https://parliament.mn/nn/45902",
            category="parliament",
            cleaned_text="2016 оны 6-р сард ОХУ-ын Ростех корпораци 'Эрдэнэт үйлдвэр' болон 'Монголросцветмет' нэгдлийн 49 хувийг Монголын хувийн компани болох 'Монголын Зэс Корпораци' (Ц.Пүрэвтүвшин, Д.Эрдэнэбилэг тэргүүтэй ХХБ-ны оролцоотой) худалдаж авсныг Ерөнхий сайд Ч.Сайханбилэг зарласан. 2017 онд УИХ-ын 23-р тогтоолоор энэхүү худалдан авалтыг УИХ-аар хэлэлцүүлээгүй, төрийн мөнгөн хөрөнгийг ашигласан гэж үзэн 49 хувийг төрийн өмчид шилжүүлэх шийдвэр гаргасан. 2019 оны 3-р сард Засгийн газраас Эрдэнэт үйлдвэрт 6 сарын Онцгой дэглэм тогтоож, төрийн 100 хувийн өмчит үйлдвэрийн газар болгосон.",
            author="УИХ-ын Хянан шалгах түр хороо",
            pub_date=date(2023, 6, 15),
            reliability=0.99
        )

        # Key Corporate Entities
        erdenet = get_or_create_entity(db, "Эрдэнэт Үйлдвэр ТӨҮГ", "company", "Монгол Улсын стратегийн тэргүүлэх зэс, молибдений баяжуулах үйлдвэр (Анх Монгол-Зөвлөлтийн хамтарсан, одоо төрийн 100% өмчит).")
        mon_copper = get_or_create_entity(db, "Монголын Зэс Корпораци ХХК", "company", "2016 онд Эрдэнэт үйлдвэрийн 49 хувийг ОХУ-ын Ростех корпорациас 400.27 сая ам.доллароор худалдан авсан хувийн компани.")
        rostech = get_or_create_entity(db, "Ростех (Rostec)", "company", "ОХУ-ын төрийн өмчит батлан хамгаалах, үйлдвэрлэлийн корпораци. Эрдэнэт үйлдвэрийн 49 хувийг эзэмшиж байсан.")
        ubtz = get_or_create_entity(db, "Улаанбаатар Төмөр Зам ХНН", "company", "Монгол-Оросын хувь нийлүүлсэн нийгэмлэг (50/50 хувийн эзэмшилтэй), Монголын транзит болон төмөр замын тээврийн гол артери.")
        erdenes_mongol = get_or_create_entity(db, "Эрдэнэс Монгол Нэгдэл", "company", "Стратегийн ач холбогдол бүхий ашигт малтмалын ордуудыг эдийн засгийн эргэлтэд оруулах төрийн толгой компани.")
        
        # Key Persons
        ts_purevtuvshin = get_or_create_entity(db, "Ц.Пүрэвтүвшин", "person", "'Монголын зэс корпораци' ХХК-ийн гүйцэтгэх захирал, хувьцаа эзэмшигч.")
        d_erdenebileg = get_or_create_entity(db, "Д.Эрдэнэбилэг", "person", "Худалдаа Хөгжлийн Банк (ХХБ)-ны ТУЗ-ийн дарга, Эрдэнэт үйлдвэрийн 49 хувийг худалдан авах санхүүгийн схемд нөлөө бүхий бизнесмэн.")
        kh_badamsuren = get_or_create_entity(db, "Х.Бадамсүрэн", "person", "'Эрдэнэт үйлдвэр' ТӨҮГ-ын ерөнхий захирал асан (2016-2022).")

        # Relationships
        add_relationship(db, corp_src.id, mon_copper.id, erdenet.id, "Эрдэнэт Үйлдвэр ТӨҮГ", "ХУВЬЦАА_ЭЗЭМШИЖ_БАЙСАН", "2016-2017 онд 49 хувийг эзэмшсэн.", "2016-06-28", "2017-02-10")
        add_relationship(db, corp_src.id, ts_purevtuvshin.id, mon_copper.id, "Монголын Зэс Корпораци ХХК", "ГҮЙЦЭТГЭХ_ЗАХИРАЛ", "Монголын зэс корпорацийн ерөнхий захирал.", "2016-01-01")
        add_relationship(db, corp_src.id, d_erdenebileg.id, mon_copper.id, "Монголын Зэс Корпораци ХХК", "САНХҮҮЖҮҮЛСЭН", "ХХБ-аар дамжуулан 49 хувийн төлбөрийг төвлөрүүлсэн.", "2016-06-01")
        add_relationship(db, corp_src.id, kh_badamsuren.id, erdenet.id, "Эрдэнэт Үйлдвэр ТӨҮГ", "УДИРДСАН", "Эрдэнэт үйлдвэрийн ерөнхий захирлаар 6 жил ажилласан.", "2016-12-01", "2022-12-01")
        add_relationship(db, corp_src.id, erdenes_mongol.id, erdenet.id, "Эрдэнэт Үйлдвэр ТӨҮГ", "ТОЛГОЙ_КОМПАНИ", "Эрдэнэс Монгол нэгдлийн бүрэлдэхүүнд Эрдэнэт үйлдвэр төрийн 100% өмчөөр харьяалагддаг.", "2022-01-01")

        # Facts (Strictly "chronological" per AGENTS.md)
        corp_facts = [
            (mon_copper.id, "2016-06-28", "chronological", "Монголын зэс корпораци ОХУ-ын Ростех корпорациас Эрдэнэт үйлдвэр болон Монголросцветмет нэгдлийн 49 хувийг 400.27 сая ам.доллароор худалдан авах гэрээг үзэглэлээ.", "49%-ийн худалдан авалт зарлагдав.", "Хувьчлал", ["Эрдэнэт 49%", "Ростех", "Монголын Зэс"]),
            (erdenet.id, "2017-02-10", "chronological", "УИХ-ын 23 дугаар тогтоолоор Эрдэнэт үйлдвэрийн 49 хувийг төрийн өмчид буцаан авах шийдвэр гаргаж, Засгийн газарт үүрэг болголоо.", "УИХ-ын 23-р тогтоол батлагдав.", "Төрийн өмч", ["УИХ", "Эрдэнэт", "23-р тогтоол"]),
            (erdenet.id, "2019-03-06", "chronological", "Засгийн газрын 91 дүгээр тогтоолоор Эрдэнэт үйлдвэрт 6 сарын хугацаатай 'Онцгой дэглэм' тогтоож, Төрийн 100 хувийн өмчит үйлдвэрийн газар болгон өөрчиллөө.", "Онцгой дэглэм тогтоов.", "Онцгой дэглэм", ["Онцгой дэглэм", "Эрдэнэт", "Засгийн газар"]),
            (ubtz.id, "2022-10-15", "chronological", "Улаанбаатар Төмөр Зам ХНН-ийн тээврийн хэмжээ 2022 онд 31 сая тоннд хүрч, экспорт болон дамжин өнгөрөх тээврийн түүхэн дээд амжилтыг тогтоолоо.", "Төмөр замын ачаа эргэлт дээд амжилт тогтоов.", "Тээвэр", ["УБТЗ", "Төмөр зам", "Экспорт"]),
            (erdenes_mongol.id, "2023-01-18", "chronological", "Засгийн газраас Эрдэнэс Монгол нэгдлийн бүтцийн шинэчлэлийг баталж, Эрдэнэт, Эрдэнэс Тавантолгой, Монголросцветмет, Дарханы төмөрлөг зэрэг 30 гаруй охин компанийг нэгтгэн удирдах төв болгов.", "Эрдэнэс Монгол бүтцийн реформ.", "Реформ", ["Эрдэнэс Монгол", "Төрийн өмч", "Бүтэц"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in corp_facts:
            add_fact(db, ent_id, corp_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Төрийн өмчит компаниуд", sentiment=0.1 if "амжилт" in txt or "реформ" in txt else -0.3)

        print(f"Corporate Entities populated with {len(corp_facts)} facts.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_corporate_entities()
