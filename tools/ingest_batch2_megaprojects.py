# -*- coding: utf-8 -*-
"""Багц 2: 'Тавантолгой төмөр замын нууц оффтейк гэрээ' ба 'Дарханы төмөрлөг, Хөтөлийн цемент концесс'-ийн өгөгдлийг оруулах скрипт.

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- Компаниудын эцсийн өмчлөгч, ХБ-ны зээлийн хэмжээ, нууц гэрээнүүдийг бүртгэнэ.
"""
import sys
import os
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from database import SessionLocal
from models import Source, Entity, EntityAlias, Fact, Relationship, Case, CaseLink
from services.matching import normalize_name

def get_or_create_entity(db, name, entity_type="person", aliases=None, description=None):
    norm = normalize_name(name)
    alias_obj = db.query(EntityAlias).filter(EntityAlias.alias_norm == norm).first()
    if alias_obj:
        return alias_obj.entity
    
    ent = db.query(Entity).filter(Entity.name == name).first()
    if ent:
        return ent

    ent = Entity(name=name, entity_type=entity_type, description=description, is_stub=False)
    db.add(ent)
    db.flush()

    db.add(EntityAlias(entity_id=ent.id, alias=name, alias_norm=norm, kind="primary"))
    if aliases:
        for a in aliases:
            anorm = normalize_name(a)
            if not db.query(EntityAlias).filter(EntityAlias.entity_id == ent.id, EntityAlias.alias_norm == anorm).first():
                db.add(EntityAlias(entity_id=ent.id, alias=a, alias_norm=anorm, kind="alias"))
    db.flush()
    return ent

def create_source(db, title, url, selected_text, category="media"):
    import hashlib
    sha256 = hashlib.sha256(selected_text.encode("utf-8")).hexdigest()
    src = db.query(Source).filter(Source.sha256_hash == sha256).first()
    if not src:
        src = Source(
            source_type="document" if not url else "article",
            title=title,
            url=url,
            category=category,
            cleaned_text=selected_text,
            selected_text=selected_text,
            sha256_hash=sha256,
            reliability_score=0.9,
            bias_score=0.0
        )
        db.add(src)
        db.flush()
    return src

def add_fact(db, entity_id, source_id, fact_text, fact_type="chronological", fact_date=None, date_precision="year", tags=None, role_context=None, sentiment_score=-0.6):
    existing = db.query(Fact).filter(Fact.entity_id == entity_id, Fact.fact_text == fact_text).first()
    if existing:
        return existing
    fact = Fact(
        entity_id=entity_id,
        source_id=source_id,
        fact_type=fact_type,
        fact_date=fact_date,
        date_precision=date_precision,
        fact_text=fact_text,
        role_context=role_context,
        sentiment_score=sentiment_score
    )
    if tags:
        fact.tags = tags
    db.add(fact)
    db.flush()
    fact.fact_id = f"F{fact.id}"
    db.flush()
    return fact

def add_rel(db, src_id, target_id, rel_type, target_name=None, source_id=None):
    existing = db.query(Relationship).filter(
        Relationship.source_entity_id == src_id,
        Relationship.target_entity_id == target_id,
        Relationship.rel_type == rel_type
    ).first()
    if existing:
        return existing
    rel = Relationship(
        source_entity_id=src_id,
        target_entity_id=target_id,
        target_name=target_name or "",
        rel_type=rel_type,
        source_id=source_id
    )
    db.add(rel)
    db.flush()
    return rel

def link_case(db, case_id, entity_id=None, fact_id=None, role="INVOLVED_IN", note=None):
    if entity_id:
        existing = db.query(CaseLink).filter(CaseLink.case_id == case_id, CaseLink.entity_id == entity_id).first()
        if existing:
            return existing
    if fact_id:
        existing = db.query(CaseLink).filter(CaseLink.case_id == case_id, CaseLink.fact_id == fact_id).first()
        if existing:
            return existing
    cl = CaseLink(case_id=case_id, entity_id=entity_id, fact_id=fact_id, role=role, note=note)
    db.add(cl)
    db.flush()
    return cl

def main():
    db = SessionLocal()
    try:
        print("=== 1. Тавантолгой төмөр замын нууц оффтейк & Нүүрсний хулгайн сүлжээ ===")
        # Case 1 (coal-theft) & Case 8 (railway-dispute)
        src_railway = create_source(
            db,
            title="Тавантолгой-Гашуунсухайт төмөр замын оффтейк нууц гэрээнүүд ба Нүүрсний түр хорооны сонсголын тайлан",
            url="https://parliament.mn/hearing/coal-hearing-2023",
            selected_text="2019 онд 'Эрдэнэс Тавантолгой' ХК болон 'Тавантолгой Төмөр Зам' ХХК-иас 'Бодь Интернэшнл' ХХК-тай байгуулсан Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын бүтээн байгуулалтын EPC гэрээг ҮАБЗ-ийн зөвлөмж, Засгийн газрын нууц тогтоолоор шууд байгуулж, санхүүжилтийг нүүрсээр урьдчилан төлөх 1 тэрбум ам.доллар давсан оффтейк нөхцөлөөр гүйцэтгэсэн нь нүүрсний экспортын үнийн зөрүү, татварын орлого алдагдах томоохон схемийн гол суурь болсон.",
            category="document"
        )

        ent_bodi = get_or_create_entity(db, "Бодь Интернэшнл ХХК", entity_type="company", aliases=["Бодь Интернэшнл", "Bodi International"], description="Төмөр замын оффтейк гэрээний ерөнхий гүйцэтгэгч")
        ent_l_bayasgalan = get_or_create_entity(db, "Лувсанвандангийн Баясгалан", entity_type="person", aliases=["Л.Баясгалан", "Бодийн Баясгалан"], description="Бодь группийн ерөнхийлөгч, үүсгэн байгуулагч")
        ent_ett = get_or_create_entity(db, "Эрдэнэс Тавантолгой ХК", entity_type="company", aliases=["ЭТТ", "Erdenes Tavantolgoi"])
        ent_tttz = get_or_create_entity(db, "Тавантолгой Төмөр Зам ХХК", entity_type="company", aliases=["ТТТЗ"])
        ent_b_gankhuyag = get_or_create_entity(db, "Баттулгын Ганхуяг", entity_type="person", aliases=["Б.Ганхуяг"], description="Эрдэнэс Тавантолгой ХК-ийн гүйцэтгэх захирал асан")
        ent_b_ganbat = get_or_create_entity(db, "Булгантуяагийн Ганбат", entity_type="person", aliases=["Б.Ганбат"], description="Тавантолгой төмөр зам ХХК-ийн захирал асан")

        # Relationships
        add_rel(db, ent_l_bayasgalan.id, ent_bodi.id, "эцсийн өмчлөгч / захирал", "Бодь Интернэшнл ХХК", source_id=src_railway.id)
        add_rel(db, ent_ett.id, ent_bodi.id, "нууц оффтейк гэрээ байгуулагч", "Бодь Интернэшнл ХХК", source_id=src_railway.id)
        add_rel(db, ent_b_gankhuyag.id, ent_ett.id, "гүйцэтгэх захирал (2018-2022)", "Эрдэнэс Тавантолгой ХК", source_id=src_railway.id)
        add_rel(db, ent_b_ganbat.id, ent_tttz.id, "гүйцэтгэх захирал", "Тавантолгой Төмөр Зам ХХК", source_id=src_railway.id)

        # Facts
        f_bodi = add_fact(db, ent_bodi.id, src_railway.id,
            "2019 оны 10-р сарын 29-нд Тавантолгой-Гашуунсухайт чиглэлийн 233.6 км төмөр замын цогцолбор төслийн EPC гэрээг ҮАБЗ-ийн зөвлөмж, Засгийн газрын нууц тогтоолын дагуу өрсөлдөөнгүйгээр 1 тэрбум 68 сая ам.долларын төсөвтэйгээр нүүрсээр төлбөр авах оффтейк нөхцөлөөр байгуулсан.",
            fact_date=date(2019, 10, 29), date_precision="day", tags=["оффтейк", "төмөр зам", "нүүрс", "нууц гэрээ"])

        f_gankhuyag = add_fact(db, ent_b_gankhuyag.id, src_railway.id,
            "Эрдэнэс Тавантолгой ХК-ийн гүйцэтгэх захирлаар ажиллах хугацаандаа нүүрсний хэд хэдэн нууц оффтейк гэрээ, тээврийн С зөвшөөрөл олголт, үнийн хөнгөлөлттэй хууль бус шийдвэрүүдээр бусдад давуу байдал олгож үндэслэлгүй хөрөнгөжсөн хэргээр яллагдаж, анхан шатны шүүхээс 5 жил 9 сарын хорих ял шийтгүүлсэн.",
            fact_date=date(2024, 2, 5), date_precision="day", tags=["нүүрсний хулгай", "ял", "оффтейк", "авлига"])

        # Link to Case 1 (coal-theft) & Case 8 (railway-dispute)
        link_case(db, 1, entity_id=ent_l_bayasgalan.id, role="BENEFICIARY", note="Бодь группийн ерөнхийлөгч, 1 тэрбум ам.долларын оффтейк гэрээний тал")
        link_case(db, 1, fact_id=f_bodi.id, role="EVIDENCE_FOR", note="1 тэрбум ам.долларын нууц оффтейк гэрээний факт")
        link_case(db, 1, fact_id=f_gankhuyag.id, role="EVIDENCE_FOR", note="Б.Ганхуягийн ялын тогтоол")

        link_case(db, 8, entity_id=ent_bodi.id, role="BENEFICIARY", note="Тавантолгой-Гашуунсухайт төмөр замыг барьж дуусгасан оффтейк гүйцэтгэгч")
        link_case(db, 8, entity_id=ent_l_bayasgalan.id, role="BENEFICIARY", note="Бодь группийн өмчлөгч")
        link_case(db, 8, fact_id=f_bodi.id, role="EVIDENCE_FOR", note="Төмөр замын оффтейк гэрээний санхүүжилт")

        print("=== 2. Дарханы төмөрлөг, Хөтөлийн цемент шохой & Сахал Эрдэнэбилэгийн схем ===")
        # Case 15 (darkhan-metallurgy) & Case 2 (dbm-scandal)
        src_erdenebileg = create_source(
            db,
            title="Дарханы төмөрлөгийн үйлдвэрийн концесс, Хөгжлийн банкны зээл ба Сахал Д.Эрдэнэбилэгийн санхүүгийн сүлжээ",
            url="https://shukh.mn/case/qsc-darkhan-metallurgy",
            selected_text="Худалдаа Хөгжлийн Банкны ТУЗ-ийн дарга Д.Эрдэнэбилэгийн хамаарал бүхий 'Кью Эс Си' (QSC) ХХК нь 2014 онд Дарханы төмөрлөгийн үйлдвэрийг концессын гэрээгээр авч, Хөгжлийн банкнаас 71 сая ам.доллар (200+ тэрбум төгрөг), Төрийн банкнаас их хэмжээний зээл авсан боловч үйлдвэрлэлийг өргөтгөх үүргээ биелүүлэлгүй төмрийн хүдрийг боловсруулалтгүй экспортолж, зээлийг төлөөгүй чанаргүйдүүлсэн үндэслэлээр төр 2022 онд концессыг цуцалж, Д.Эрдэнэбилэг хилийн чанад руу гарсан.",
            category="document"
        )

        ent_d_erdenebileg = get_or_create_entity(db, "Далхаасүрэнгийн Эрдэнэбилэг", entity_type="person", aliases=["Д.Эрдэнэбилэг", "Сахал Эрдэнэбилэг"], description="ХХБ-ны ТУЗ-ийн дарга асан, QSC болон Эрдэнэт 49-ийн гол санхүүжүүлэгч")
        ent_qsc = get_or_create_entity(db, "Кью Эс Си ХХК", entity_type="company", aliases=["QSC LLC", "QSC"], description="Дарханы төмөрлөгийн үйлдвэрийн концесс эзэмшигч, ХБ-ны хамгийн том чанаргүй зээлдэгч")
        ent_cement = get_or_create_entity(db, "Хөтөлийн цемент шохой ХХК", entity_type="company", aliases=["Цемент Шохой", "Хөтөл цемент"], description="Хөгжлийн банкны чанаргүй зээлдэгч компани")
        ent_darkhan_factory = get_or_create_entity(db, "Дарханы Төмөрлөгийн Үйлдвэр ТӨХК", entity_type="company", description="Төмрийн хүдэр боловсруулах төрийн өмчит үйлдвэр")
        ent_tdb = get_or_create_entity(db, "Худалдаа Хөгжлийн Банк", entity_type="company", aliases=["ХХБ", "TDB"])

        # Relationships
        add_rel(db, ent_d_erdenebileg.id, ent_qsc.id, "эцсийн өмчлөгч / удирдагч", "Кью Эс Си ХХК", source_id=src_erdenebileg.id)
        add_rel(db, ent_d_erdenebileg.id, ent_tdb.id, "ТУЗ-ийн дарга / хувьцаа эзэмшигч", "Худалдаа Хөгжлийн Банк", source_id=src_erdenebileg.id)
        add_rel(db, ent_d_erdenebileg.id, ent_cement.id, "эцсийн хяналт тавигч", "Хөтөлийн цемент шохой ХХК", source_id=src_erdenebileg.id)
        add_rel(db, ent_qsc.id, ent_darkhan_factory.id, "концесс эзэмшигч (2014-2022)", "Дарханы Төмөрлөгийн Үйлдвэр", source_id=src_erdenebileg.id)

        # Facts
        f_qsc = add_fact(db, ent_qsc.id, src_erdenebileg.id,
            "2014-2015 онд Хөгжлийн банкнаас 71.3 сая ам.доллар болон 68 тэрбум төгрөгийн зээлийг Дарханы төмөрлөгийн үйлдвэрийг өргөтгөх нэрээр авсан боловч зээлээ зориулалтын бусаар зарцуулж, эргэн төлөлт хийгээгүй улсад 200 гаруй тэрбум төгрөгийн бодит хохирол учруулсан.",
            fact_date=date(2014, 12, 1), date_precision="month", tags=["Хөгжлийн банк", "чанаргүй зээл", "концесс", "хохирол"])

        f_erdenebileg = add_fact(db, ent_d_erdenebileg.id, src_erdenebileg.id,
            "Эрдэнэт үйлдвэрийн 49 хувийг хууль бусаар хувьчилсан схем болон QSC, Дарханы төмөрлөг, Хөгжлийн банкны их хэмжээний зээлийн хэрэгт яллагдагчаар татагдан 3 тэрбум төгрөгийн барьцаа байршуулан суллагдсаны дараа эмчилгээ хийлгэх нэрийдлээр Сингапур улс руу гарч хэрэг хянан шийдвэрлэх ажиллагаанаас зайлсхийсэн.",
            fact_date=date(2022, 5, 20), date_precision="day", tags=["Эрдэнэт 49", "зугтсан", "Хөгжлийн банк", "авлига"])

        f_cancel_concession = add_fact(db, ent_darkhan_factory.id, src_erdenebileg.id,
            "2022 оны 4-р сард Засгийн газрын шийдвэрээр 'Кью Эс Си' ХХК-тай байгуулсан концессын гэрээг үүргээ биелүүлээгүй, төмрийн хүдрийг үнэгүйдүүлэн гаргасан үндэслэлээр цуцалж, үйлдвэрийн үйл ажиллагааг төрийн мэдэлд буцаан авсан.",
            fact_date=date(2022, 4, 13), date_precision="day", tags=["концесс", "цуцлалт", "төрийн өмч"])

        # Link to Case 15 (darkhan-metallurgy) & Case 2 (dbm-scandal) & Case 7 (erdenet-49)
        link_case(db, 15, entity_id=ent_d_erdenebileg.id, role="DECISION_MAKER", note="QSC-ийн цаад эзэмшигч, концессыг удирдсан")
        link_case(db, 15, entity_id=ent_darkhan_factory.id, role="PART_OF_CASE", note="Концесст шилжсэн төрийн өмчит үйлдвэр")
        link_case(db, 15, fact_id=f_qsc.id, role="EVIDENCE_FOR", note="Хөгжлийн банкнаас авсан зээлийн факт")
        link_case(db, 15, fact_id=f_erdenebileg.id, role="EVIDENCE_FOR", note="Д.Эрдэнэбилэгийн хэрэг ба зугталт")
        link_case(db, 15, fact_id=f_cancel_concession.id, role="EVIDENCE_FOR", note="Концесс цуцалсан Засгийн газрын шийдвэр")

        link_case(db, 2, entity_id=ent_d_erdenebileg.id, role="BENEFICIARY", note="ХБ-ны хамгийн том чанаргүй зээлийн бүлэглэлийг удирдсан")
        link_case(db, 2, fact_id=f_qsc.id, role="EVIDENCE_FOR", note="QSC-ийн 71 сая ам.долларын чанаргүй зээл")

        link_case(db, 7, entity_id=ent_d_erdenebileg.id, role="DECISION_MAKER", note="Эрдэнэт 49 хувийн санхүүгийн схемийн гол эзэн")

        db.commit()
        print("Багц 2 амжилттай бүртгэгдлээ!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
