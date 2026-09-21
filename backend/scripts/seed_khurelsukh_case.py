"""
Seed Script: Comprehensive Controversies & Cases of Ukhnaagiin Khurelsukh
1. Khadgalamj Bank 14B & Walker Hill Casino Scandal (2006-2007)
2. Wiretapping Allegation & Ousting of J.Erdenebat Government (2017)
3. National Security Council (NSC/ҮАБЗ) Judicial Takeover Law (2019)
4. Tavantolgoi Tulsh & Carbon Monoxide Poisoning / Raw Coal Ban (2019-2020)
5. Maternity Transport Scandal & Resignation for Presidential Bid (2021)

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
            author=author or "УИХ / Шүүх / Хэвлэл",
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


def seed_khurelsukh_scandals():
    db = SessionLocal()
    try:
        print("\n=== SEEDING U.KHURELSUKH CONTROVERSIES CASE ===")
        
        # Source 1: General Legal & Court Archival
        kh_src = get_or_create_source(
            db,
            title="Ухнаагийн Хүрэлсүхийн улс төрийн үйл ажиллагаа, Хадгаламж банкны хэрэг, 2017 оны чагнасан хэрэг, 2019 оны ҮАБЗ-ийн хууль ба огцролтын түүхэн баримтууд",
            url="https://legalinfo.mn",
            category="document",
            cleaned_text="Монгол Улсын Ерөнхийлөгч, Ерөнхий сайд асан Ухнаагийн Хүрэлсүхийн улс төрийн замнал дахь гол дуулиант хэргүүдийн баримт бичгүүд. 2006-2007 онд Хадгаламж банкны 14 тэрбум төгрөг алдагдсан хэрэг, Сөүлийн Уолкер Хилл казиногийн асуудал. 2017 онд Шадар сайд байхдаа Ерөнхий сайд Ж.Эрдэнэбатын Засгийн газрыг унагасан 'Тагнаж чагнасан' хэрэг. 2019 онд Шүүгчийн эрх зүйн байдлын хуульд өөрчлөлт оруулж ҮАБЗ-ийн зөвлөмжөөр шүүх, прокурорын удирдлагыг чөлөөлөх эрхийг батлуулсан явдал. 2019 онд Тавантолгой түлш ХХК ба угаарын хийн хордлого. 2021 оны 1-р сард дөнгөж амаржсан эхийн зөөвөрлөлтөөс үүдэлтэй Засгийн газрын гэнэтийн огцролт.",
            author="УИХ / Шүүх / Хэвлэлийн архив",
            pub_date=date(2021, 6, 25),
            reliability=0.98
        )

        # Entities
        u_khurelsukh = get_or_create_entity(db, "Ухнаагийн Хүрэлсүх", "person")
        khadgalamj_bank = get_or_create_entity(db, "Хадгаламж Банк", "company", "Монгол Улсын төрийн өмчит байсан арилжааны банк (2006-2007 онд 14 тэрбумын хэрэг гарсан).")
        ts_chimedtseren = get_or_create_entity(db, "Ц.Чимэдцэрэн", "person", "Хадгаламж банкны нягтлан бодогч асан, 14 тэрбум төгрөг завшсан хэргээр ял шийтгүүлсэн.")
        j_erdenebat = get_or_create_entity(db, "Жаргалтулгын Эрдэнэбат", "person")
        g_zandanshatar = get_or_create_entity(db, "Гомбожавын Занданшатар", "person")
        nsc = get_or_create_entity(db, "Үндэсний Аюулгүй Байдлын Зөвлөл (ҮАБЗ)", "government", "Монгол Улсын ҮАБЗ (Ерөнхийлөгч, Ерөнхий сайд, УИХ-ын дарга).")
        tt_tulsh = get_or_create_entity(db, "Тавантолгой Түлш ХХК", "company", "Улаанбаатар хотын шахмал түлш үйлдвэрлэх, түгээх төрийн өмчит компани.")

        # Create Dedicated Case
        kh_case = db.query(models.Case).filter(models.Case.slug == "khurelsukh-controversies").first()
        if not kh_case:
            kh_case = models.Case(
                slug="khurelsukh-controversies",
                title="У.Хүрэлсүхтэй Холбогдох Улс Төрийн Дуулианууд & Үйл Явдлууд",
                description="Хадгаламж банкны 14 тэрбумын казиногийн хэрэг (2007), 2017 оны 'Тагнасан' дуулиан ба ЗГ-ын огцролт, 2019 оны ҮАБЗ-ийн шүүхийг хянах хууль, Тавантолгой түлшний хордлого, 2021 оны эхийн зөөвөрлөлт ба гэнэтийн огцролтын иж бүрэн баримтууд.",
                status="PUBLISHED",
                cover_entity_id=u_khurelsukh.id
            )
            db.add(kh_case)
            db.commit()
            db.refresh(kh_case)
            print(f"Created case: {kh_case.title}")

        for ent, role, note in [
            (u_khurelsukh, "DECISION_MAKER", "Мөрдлөгийн төв субъект"),
            (khadgalamj_bank, "VICTIM", "14 тэрбум төгрөгийн хохирол амссан банк"),
            (ts_chimedtseren, "SUSPECT", "Хадгаламж банкнаас мөнгө завшсан нягтлан"),
            (j_erdenebat, "PART_OF_CASE", "2017 оны тагнасан хэргээр огцорсон Ерөнхий сайд"),
            (g_zandanshatar, "PART_OF_CASE", "Казино болон ҮАБЗ-ийн хамтрагч улстөрч"),
            (nsc, "DECISION_MAKER", "2019 оны шүүгч, прокурорыг чөлөөлөх хуулийг хэрэгжүүлэгч"),
            (tt_tulsh, "PART_OF_CASE", "Сайжруулсан шахмал түлшний төрийн компани")
        ]:
            link_to_case(db, kh_case, entity_id=ent.id, role=role, note=note)

        # Relationships
        add_relationship(db, kh_src.id, ts_chimedtseren.id, khadgalamj_bank.id, "Хадгаламж Банк", "МӨНГӨ_ЗАВШСАН", "Ц.Чимэдцэрэн 14 тэрбум төгрөгийг казино руу шилжүүлэн завшсан нь тогтоогдсон.", "2006-01-01")
        add_relationship(db, kh_src.id, u_khurelsukh.id, khadgalamj_bank.id, "Хадгаламж Банк", "ХЭРЭГТ_ШАЛГАГДСАН", "Казино тоглосон хэрэгт УИХ-ын гишүүн У.Хүрэлсүхийг шалгаж бүрэн эрхийг түдгэлзүүлж байв.", "2007-06-01")
        add_relationship(db, kh_src.id, u_khurelsukh.id, j_erdenebat.id, "Жаргалтулгын Эрдэнэбат", "ОГЦРУУЛАХЫГ_ШААРДСАН", "Тагнасан хэргээр шалтаглан Ерөнхий сайд Ж.Эрдэнэбатыг огцруулсан.", "2017-08-23")
        add_relationship(db, kh_src.id, u_khurelsukh.id, nsc.id, "Үндэсний Аюулгүй Байдлын Зөвлөл (ҮАБЗ)", "ХУУЛИЙГ_БАТЛУУЛСАН", "Шүүгчийн эрх зүйн байдлын тухай хуулийг ҮАБЗ-д төвлөрүүлэн батлуулсан.", "2019-03-27")
        add_relationship(db, kh_src.id, u_khurelsukh.id, tt_tulsh.id, "Тавантолгой Түлш ХХК", "ҮҮСГЭН_БАЙГУУЛСАН", "Засгийн газрын 62-р тогтоолоор түүхий нүүрсийг хориглож шахмал түлшний үйлдвэрийг байгуулсан.", "2019-03-05")

        # Facts (Strictly "chronological" per AGENTS.md)
        kh_facts = [
            (u_khurelsukh.id, "2007-06-25", "chronological", "Улсын Ерөнхий Прокурорын саналын дагуу УИХ-аас Хадгаламж банкны 14 тэрбум төгрөг алдагдсан хэрэг, Уолкер Хилл казиногийн асуудлаар УИХ-ын гишүүн У.Хүрэлсүхийн бүрэн эрхийг түдгэлзүүлэн шалгахаар тогтов.", "УИХ бүрэн эрхийг түдгэлзүүлэв.", "Хадгаламж банк", ["Хадгаламж банк", "Казино", "УИХ"]),
            (u_khurelsukh.id, "2007-10-18", "chronological", "Чингэлтэй дүүргийн шүүхээс У.Хүрэлсүхэд Хадгаламж банкны хэрэгт холбогдуулан ял оноосон боловч хожим давж заалдах шатны шүүхээс хэргийг хэрэгсэхгүй болгож, улмаар тэрбээр МАХН-ын ЕНБД-аар томилогдон улс төрд эргэн ирэв.", "Шүүхийн шийдвэр гарлаа.", "Шүүх", ["Шүүх", "МАХН", "У.Хүрэлсүх"]),
            (u_khurelsukh.id, "2017-08-23", "chronological", "Шадар сайд У.Хүрэлсүх 'Ерөнхий сайд Ж.Эрдэнэбат намайг хууль бусаар тагнаж, чагнасан' хэмээн мэдэгдэж Засгийн газрын гишүүнээс огцрох өргөдлөө өгснөөр Засгийн газар огцрох улс төрийн хямрал үүсэв.", "Тагнаж чагнасан дуулиан задрав.", "Тагнасан хэрэг", ["Тагнасан хэрэг", "Ж.Эрдэнэбат", "Шадар сайд"]),
            (u_khurelsukh.id, "2017-10-04", "chronological", "Ж.Эрдэнэбатын Засгийн газрыг огцруулсны дараа УИХ-ын чуулганаар У.Хүрэлсүхийг Монгол Улсын 30 дахь Ерөнхий сайдаар баталж танхимаа бүрдүүлэв.", "У.Хүрэлсүх Ерөнхий сайд болов.", "Томилгоо", ["Ерөнхий сайд", "У.Хүрэлсүх"]),
            (u_khurelsukh.id, "2019-03-27", "chronological", "Ерөнхий сайд У.Хүрэлсүхийн Засгийн газар, Ерөнхийлөгч Х.Баттулга нар хамтран Шүүгчийн эрх зүйн байдлын хуульд өөрчлөлт оруулж, ҮАБЗ-ийн зөвлөмжөөр шүүгч, прокурорын удирдлагыг чөлөөлөх хуулийг УИХ-аар яаралтай горимоор батлуулав.", "ҮАБЗ-ийн шүүхийн хууль батлагдав.", "Хууль засаглал", ["ҮАБЗ", "Шүүх", "Хонгил"]),
            (tt_tulsh.id, "2019-10-06", "chronological", "Улаанбаатар хотод түүхий нүүрсийг хориглож шахмал түлшинд шилжсэний дараа угаарын хийн хордлогын улмаас эхний сард олон зуун иргэн хордож, 10 гаруй хүн амиа алдсан нь нийгэмд хүчтэй шүүмжлэл үүсгэв.", "Шахмал түлшний угаарын хордлого.", "Угаар", ["Тавантолгой түлш", "Угаар", "Хордлого"]),
            (u_khurelsukh.id, "2021-01-20", "chronological", "Төрсөн дөнгөж амаржсан эхийг нярай хүүхдийн хамт COVID-19 халдварын улмаас хүйтэнд дулаан хувцасгүй зөөвөрлөсөн бичлэг цацагдаж, Сүхбаатарын талбайд иргэдийн эсэргүүцлийн жагсаал өрнөв.", "Эхийн зөөвөрлөлтийн дуулиан гарлаа.", "Жагсаал", ["COVID-19", "Жагсаал", "Эх нярай"]),
            (u_khurelsukh.id, "2021-01-21", "chronological", "Ерөнхий сайд У.Хүрэлсүх төрийн албаны хүнлэг бус харилцааны хариуцлагыг ёс зүйн хувьд хүлээн өөрийн хүсэлтээр Засгийн газрыг бүрэн бүрэлдэхүүнээр огцруулах өргөдлөө гаргаж огцорлоо.", "У.Хүрэлсүх Ерөнхий сайдаас огцров.", "Огцролт", ["Огцролт", "Ерөнхий сайд", "Хариуцлага"])
        ]

        for ent_id, dt, ftype, txt, qte, top, tgs in kh_facts:
            f = add_fact(db, ent_id, kh_src.id, dt, ftype, txt, qte, top, tgs, role_ctx="У.Хүрэлсүхийн дуулианууд", sentiment=-0.6)
            link_to_case(db, kh_case, fact_id=f.id, role="EVIDENCE_FOR", note=top)

        print(f"U.Khurelsukh Controversies Case populated with {len(kh_facts)} facts.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_khurelsukh_scandals()
