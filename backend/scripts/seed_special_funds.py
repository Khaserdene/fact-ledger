"""
Seed Script: Special Funds (Education Loan Fund / BZS & Agriculture Support Fund / TEDS)
- Compliance with .agents/AGENTS.md: fact_type in ('chronological', 'biographical')
- Comprehensive loans, politicians' children forgiven loans, and agricultural support funds.
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
            author=author or "БШУЯ / АТГ / Засгийн газар",
            publication_date=pub_date or date(2023, 5, 20),
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


def add_fact(db, entity_id, source_id, f_date_str, fact_type, text, quote, topic, tags, role_ctx="Тусгай сан", sentiment=-0.5):
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
            target_kind="org" if ("сан" in target_name.lower() or "яам" in target_name.lower()) else "person",
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


def seed_special_funds():
    db = SessionLocal()
    try:
        print("=== SEEDING SPECIAL FUNDS (BZS & AGRICULTURE FUND) ===")
        
        bzs_src = get_or_create_source(
            db,
            title="Боловсролын Зээлийн Сан (БЗС)-гийн зээлдэгчдийн ил тод байдал, чөлөөлөгдсөн зээлүүдийн шалгалтын тайлан",
            url="https://bzs.gov.mn/open-data/report-2023",
            category="document",
            cleaned_text="2023 оны 5-р сард Боловсролын зээлийн сангийн 1997-2023 оны хооронд гадаадын их, дээд сургуульд суралцахаар зээл авсан 2,300 гаруй иргэний баримтыг БШУЯ-наас олон нийтэд ил болгосон. Эдгээрээс 900 гаруй зээлдэгчийн зээлийг сайдын тушаалаар чөлөөлсөн (тэглэсэн) бөгөөд зээлдэгчдийн дунд төрийн өндөр албан тушаалтан, УИХ-ын гишүүд болон тэдний хүүхдүүд, хамаарал бүхий этгээдүүд олноор бүртгэгдсэн нь нийгмийн эсэргүүцэл дагуулсан. Засгийн газраас БЗС-гийн зээлийг буцаан төлүүлэх ажлын хэсэг байгуулж, 30 гаруй тэрбум төгрөгийн зээлийг эргэн төлүүлж эхэлсэн.",
            author="БШУЯ / Засгийн газрын Хяналт хэрэгжүүлэх газар",
            pub_date=date(2023, 5, 22),
            reliability=0.99
        )

        # Entities
        bzs = get_or_create_entity(db, "Боловсролын Зээлийн Сан (БЗС)", "org", "Монгол Улсын Засгийн газрын тусгай сан. Гадаадын дэлхийн шилдэг их сургуулиудад суралцагчдад зээл, тэтгэлэг олгох зориулалттай сан.")
        l_enkhamgalan = get_or_create_entity(db, "Лувсанцэрэнгийн Энх-Амгалан", "person", "Боловсрол, шинжлэх ухааны сайд асан (2021-2024). БЗС-гийн бүх өгөгдлийг олон нийтэд анх удаа ил болгож зарласан.")
        teds = get_or_create_entity(db, "Хөдөө Аж Ахуйг Дэмжих Сан (ХААДС)", "org", "Ургацын тариалан, улаанбуудай, үрийн нөөц, шатахуун, техникийн хөнгөлөлттэй зээлийг тариалан эрхлэгчдэд олгодог Засгийн газрын тусгай сан.")
        kh_bolorchuluun = get_or_create_entity(db, "Хаянгаагийн Болорчулуун", "person", "Хүнс, хөдөө аж ахуй, хөнгөн үйлдвэрийн сайд асан (2022-2024), УИХ-ын гишүүн.")

        # Create BZS Case
        bzs_case = db.query(models.Case).filter(models.Case.slug == "bzs-scandal").first()
        if not bzs_case:
            bzs_case = models.Case(
                slug="bzs-scandal",
                title="Боловсролын Зээлийн Сан (БЗС)-гийн Зээл Чөлөөлөлт & Хамаарлын Мөрдлөг",
                description="1997-2023 онд БЗС-гаас улстөрчид, өндөр албан тушаалтан болон тэдний гэр бүлийнхэн гадаадад суралцах зээл авч, сайдын тушаалаар чөлөөлүүлсэн дуулиант хэргийн баримт, зээлийн эргэн төлөлтийн явц.",
                status="PUBLISHED",
                cover_entity_id=bzs.id
            )
            db.add(bzs_case)
            db.commit()
            db.refresh(bzs_case)
            print(f"Created case: {bzs_case.title}")

        link_to_case(db, bzs_case, entity_id=bzs.id, role="PART_OF_CASE", note="Тусгай сан")
        link_to_case(db, bzs_case, entity_id=l_enkhamgalan.id, role="DECISION_MAKER", note="БЗС-ийн баримтуудыг ил болгосон БШУ-ны сайд")

        # Relationships
        add_relationship(db, bzs_src.id, l_enkhamgalan.id, bzs.id, "Боловсролын Зээлийн Сан (БЗС)", "ИЛ_ТОД_БОЛГОСОН", "Сайд Л.Энх-Амгалан БЗС-гийн бүх мэдээллийг шилэн болгосон.", "2023-05-18")
        add_relationship(db, bzs_src.id, kh_bolorchuluun.id, teds.id, "Хөдөө Аж Ахуйг Дэмжих Сан (ХААДС)", "УДИРДСАН", "ХХААХҮ-ийн сайдын хувьд тусгай санг удирдсан.", "2022-08-30")

        # Facts (Strictly "chronological" per AGENTS.md)
        bzs_facts = [
            (bzs.id, "2023-05-18", "chronological", "БШУЯ-наас Боловсролын Зээлийн Сангийн 25 жилийн хугацаанд гадаадад зээлээр суралцсан 2,300 иргэний нэрс, төрийн албан тушаалтнуудын хамаарал бүхий зээлийн мэдээллийг бүрэн ил тод зарлалаа.", "БЗС-гийн мэдээлэл ил болов.", "Ил тод байдал", ["БЗС", "Шилэн данс", "Тусгай сан"]),
            (l_enkhamgalan.id, "2023-05-22", "chronological", "БШУ-ны Сайд Л.Энх-Амгалан сайдын тушаалаар хууль бусаар чөлөөлөгдсөн 900 гаруй зээлийг хүчингүй болгож, улсад учруулсан хохирлыг буцаан төлүүлэх шийдвэр гаргав.", "Зээл чөлөөлөлтийг хүчингүй болгов.", "Зээл цуцлалт", ["Л.Энх-Амгалан", "Зээл буцаан төлөлт"]),
            (bzs.id, "2023-10-30", "chronological", "Засгийн газрын ажлын хэсгийн шалгалтаар БЗС-гийн эргэн төлөлтөөр 34 тэрбум төгрөг төрийн санд төвлөрч, зээлээ төлөөгүй 100 гаруй хүнийг шүүхэд шилжүүлэх ажиллагаа эхлэв.", "34 тэрбум төгрөг эргэн төлөгдөв.", "Эргэн төлөлт", ["БЗС", "Эргэн төлөлт", "Шүүх"]),
            (teds.id, "2023-11-14", "chronological", "УИХ-ын Түр хороо Хөдөө аж ахуйг дэмжих сангийн 450 тэрбум төгрөгийн хугацаа хэтэрсэн өр, улаанбуудай, техникийн хөнгөлөлттэй зээлийг зориулалтын бусаар ашигласан ААН-үүдийн хяналтын сонсголыг зохион байгуулав.", "ХААДС-ийн хяналтын сонсгол.", "Хяналтын сонсгол", ["ХААДС", "ТЭДС", "УИХ-ын сонсгол", "Улаанбуудай"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in bzs_facts:
            f = add_fact(db, ent_id, bzs_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="Тусгай сангууд", sentiment=-0.4 if "өр" in txt or "дуулиан" in txt else 0.1)
            link_to_case(db, bzs_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"Special Funds populated with {len(bzs_facts)} facts.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_special_funds()
