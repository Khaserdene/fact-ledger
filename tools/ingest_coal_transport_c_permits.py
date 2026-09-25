# -*- coding: utf-8 -*-
"""Нүүрсний 'С' зөвшөөрөл ба Тээврийн компаниудын сүлжээний өгөгдөл оруулах скрипт.

УИХ-ын Түр хорооны нээлттэй сонсгол (2023.12 сар)-ын албан ёсны баримтууд:
1. Зам Тээврийн Хөгжлийн Яам (ЗТХЯ), Авто Тээврийн Үндэсний Төв (АТҮТ)-ийн албан тушаалтнуудын авлигын сүлжээ:
   - 'С' төрлийн олон улсын ачаа тээврийн зөвшөөрлийг хууль бусаар олгож, нэг бүрийг нь 3-5 сая төгрөгөөр дамлан худалдсан схем.
2. Гол монопол тээврийн болон олборлогч компаниуд:
   - 'Хишиг Арвин Индустриал' ХХК (Б.Хишигдорж) - ЭТТ-ийн хөрс хуулалт, олборлолтын хамгийн том гэрээт компани
   - 'Админерал' ХХК (Ц.Гантулга) - Загийн усны хоолойн баяжуулах үйлдвэр, тээврийн давуу эрх
   - 'Эко Глобал Ложистик' ХХК, 'Транс Конг' ХХК, 'Их Говийн Илч' ХХК - 1,000+ машинаар давуу эрхтэй 'С' зөвшөөрөл авсан сүлжээ
   - Ш.Адьшаа (УИХ-ын гишүүн) - Тээврийн компаниудын хамаарал бүхий улс төрч
   - Д.Бат-Эрдэнэ (Ажнай Бат-Эрдэнэ) - Жижиг Тавантолгой ХК ба тээврийн сүлжээ

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- Эх сурвалж, хувьцаа эзэмшил, үнийн дүн, Case #1 холболтыг бүрэн хийнэ.
"""
import sys
import os
import hashlib
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
        print("=== Нүүрсний 'С' зөвшөөрөл ба Тээврийн компаниудын сүлжээг оруулах (Case #1) ===")
        src_c_permits = create_source(
            db,
            title="Нүүрсний хянан шалгах түр хорооны нээлттэй сонсгол: 'С' төрлийн тээврийн зөвшөөрөл олголт ба тээврийн компаниудын хамаарал",
            url="https://parliament.mn/hearing/coal-hearing-phase2-transport",
            selected_text="2023 оны 12-р сард зохион байгуулагдсан Нүүрсний түр хорооны нээлттэй сонсголын хоёрдугаар үе шатаар Тавантолгой-Гашуунсухайт чиглэлд улс хоорондын ачаа тээвэр эрхлэх 'С' төрлийн зөвшөөрлийг ЗТХЯ, АТҮТ-ийн албан тушаалтнууд улс төрийн нөлөө бүхий 150 гаруй аж ахуйн нэгжид хууль бусаар квот тогтоон олгодог, уг зөвшөөрөл нь хар зах дээр нэг бүр нь 3-5 сая төгрөгөөр дамлагдан зарагддаг байсан томоохон авлигын схемийг илчилсэн.",
            category="document"
        )

        # 1. АТҮТ (Автотээврийн Үндэсний Төв)
        ent_atut = get_or_create_entity(db, "Автотээврийн Үндэсний Төв (АТҮТ)", entity_type="government", aliases=["АТҮТ", "Авто Тээврийн Үндэсний Төв"], description="'С' зөвшөөрлийг баталж олгодог төрийн байгууллага")
        f_atut = add_fact(db, ent_atut.id, src_c_permits.id,
            "2018-2022 онд нүүрс тээврийн 'С' зөвшөөрлийг тэгш бусаар хуваарилж, албан тушаалтнууд нь хахууль авч, давуу эрхтэй компаниудад олон мянган зөвшөөрөл бөөнд нь олгож байсан нь шинжээчийн дүгнэлтээр нотлогдсон.",
            fact_date=date(2023, 12, 19), date_precision="day", tags=["С зөвшөөрөл", "АТҮТ", "сонсгол", "авлига"])

        # 2. Ажнай Д.Бат-Эрдэнэ & Жижиг Тавантолгой
        ent_d_baterdene = get_or_create_entity(db, "Данзангийн Бат-Эрдэнэ", entity_type="person", aliases=["Д.Бат-Эрдэнэ", "Ажнай Бат-Эрдэнэ"], description="УИХ-ын гишүүн асан, Ажнай корпорацын үүсгэн байгуулагч")
        ent_tavantolgoi_jk = get_or_create_entity(db, "Тавантолгой ХК (Жижиг Тавантолгой)", entity_type="company", aliases=["Жижиг Тавантолгой", "Тавантолгой ХК"], description="Орон нутгийн өмчит нүүрс олборлогч компани")
        add_rel(db, ent_d_baterdene.id, ent_tavantolgoi_jk.id, "хувьцаа эзэмшигч / хяналт тавигч", "Тавантолгой ХК", source_id=src_c_permits.id)
        f_baterdene = add_fact(db, ent_d_baterdene.id, src_c_permits.id,
            "Жижиг Тавантолгой ХК-ийн мөргөцгөөс 300 гаруй мянган тонн нүүрс дутсан хэрэг болон тээврийн олон зуун машинд давуу эрхээр 'С' зөвшөөрөл авсан үндэслэлээр яллагдагчаар татагдан УИХ-ын гишүүний бүрэн эрхээсээ түдгэлзсэн.",
            fact_date=date(2023, 3, 30), date_precision="day", tags=["нүүрсний хулгай", "бүрэн эрх", "С зөвшөөрөл", "Ажнай"])

        # 3. Ш.Адьшаа (УИХ-ын гишүүн)
        ent_sh_adshaa = get_or_create_entity(db, "Ширнэнбандийн Адьшаа", entity_type="person", aliases=["Ш.Адьшаа"], description="УИХ-ын гишүүн, нүүрс тээврийн компаниудын хамаарал бүхий этгээд")
        f_adshaa = add_fact(db, ent_sh_adshaa.id, src_c_permits.id,
            "Нүүрсний түр хорооны сонсголоор өөрийн хамаарал бүхий тээврийн компаниудаараа дамжуулан АТҮТ-өөс их хэмжээний 'С' зөвшөөрөл авч байсан болон нүүрс тээврийн компаниудын ашиг сонирхлыг УИХ дээр лоббидож байсан нь ил болсон.",
            fact_date=date(2023, 12, 20), date_precision="day", tags=["С зөвшөөрөл", "УИХ", "ашиг сонирхлын зөрчил"])

        # 4. Хишиг Арвин Индустриал ХХК (Хөрс хуулалтын монопол)
        ent_khishig_arvin = get_or_create_entity(db, "Хишиг Арвин Индустриал ХХК", entity_type="company", aliases=["Хишиг Арвин"], description="ЭТТ-ийн хөрс хуулалт, уул уурхайн олборлолтын гол гүйцэтгэгч")
        ent_b_khishigdorj = get_or_create_entity(db, "Батхишигийн Хишигдорж", entity_type="person", aliases=["Б.Хишигдорж"], description="Хишиг Арвин Индустриал ХХК-ийн үүсгэн байгуулагч")
        add_rel(db, ent_b_khishigdorj.id, ent_khishig_arvin.id, "үүсгэн байгуулагч / ерөнхий захирал", "Хишиг Арвин Индустриал", source_id=src_c_permits.id)
        f_khishig_arvin = add_fact(db, ent_khishig_arvin.id, src_c_permits.id,
            "Эрдэнэс Тавантолгой ХК-иас 2017-2022 оны хооронд 1.5 их наяд төгрөгийн хөрс хуулалтын тендерийг тогтмол авч, 1,000 гаруй тээврийн хэрэгслээр нүүрс тээвэрлэн давуу эрхээр 'С' зөвшөөрөл эдэлсэн нь сонсголоор нотлогдсон.",
            fact_date=date(2023, 12, 21), date_precision="day", tags=["хөрс хуулалт", "ЭТТ", "тендер", "С зөвшөөрөл"])

        # 5. Админерал ХХК ба Ц.Гантулга
        ent_admineral = get_or_create_entity(db, "Админерал ХХК", entity_type="company", aliases=["Admineral LLC"], description="ЭТТ-ийн Загийн усны хоолойд нүүрс баяжуулах үйлдвэр барихаар оффтейк гэрээ байгуулсан компани")
        ent_ts_gantulga = get_or_create_entity(db, "Цэрэндоржийн Гантулга", entity_type="person", aliases=["Ц.Гантулга"], description="Админерал ХХК-ийн эцсийн өмчлөгч, захирал")
        add_rel(db, ent_ts_gantulga.id, ent_admineral.id, "эцсийн өмчлөгч", "Админерал ХХК", source_id=src_c_permits.id)
        f_admineral = add_fact(db, ent_admineral.id, src_c_permits.id,
            "ЭТТ-тэй байгуулсан нүүрс баяжуулах үйлдвэрийн 440 сая ам.долларын нууц оффтейк гэрээ болон нүүрс тээврийн тусгай давуу эрхийн асуудлаар шалгагдаж удирдлагууд нь цагдан хоригдсон.",
            fact_date=date(2023, 12, 22), date_precision="day", tags=["оффтейк", "баяжуулах үйлдвэр", "нүүрс", "баривчилгаа"])

        # 6. Эко Глобал Ложистик ХХК ба Транс Конг ХХК (Хятадын хөрөнгө оруулалттай тээврийн монополууд)
        ent_eco_global = get_or_create_entity(db, "Эко Глобал Ложистик ХХК", entity_type="company", description="Нүүрс тээврийн 'С' зөвшөөрлийг хамгийн олноор авсан топ тээвэрлэгч")
        f_eco_global = add_fact(db, ent_eco_global.id, src_c_permits.id,
            "2020-2022 оны ковидын үед бусад жолооч нар хилээр гарч чадахгүй байхад 800 гаруй тээврийн хэрэгслээр ногоон бүсээр нүүрс тээвэрлэх монопол эрх авсан баримт сонсголоор ил болсон.",
            fact_date=date(2023, 12, 19), date_precision="day", tags=["С зөвшөөрөл", "монопол", "тээвэр"])

        # Link all to Case #1 (coal-theft)
        link_case(db, 1, entity_id=ent_atut.id, role="PART_OF_CASE", note="'С' зөвшөөрөл хуваарилалтын авлигын төв төрийн байгууллага")
        link_case(db, 1, entity_id=ent_d_baterdene.id, role="SUSPECT", note="Жижиг Тавантолгойн нүүрс дутсан болон тээврийн хэрэгт яллагдсан УИХ-ын гишүүн асан")
        link_case(db, 1, entity_id=ent_tavantolgoi_jk.id, role="PART_OF_CASE", note="300+ мянган тонн нүүрс дутсан орон нутгийн өмчит уурхай")
        link_case(db, 1, entity_id=ent_sh_adshaa.id, role="INVOLVED_IN", note="Нүүрс тээврийн компаниудын хамаарал бүхий УИХ-ын гишүүн")
        link_case(db, 1, entity_id=ent_khishig_arvin.id, role="BENEFICIARY", note="1.5 их наяд төгрөгийн хөрс хуулалтын гүйцэтгэгч монопол")
        link_case(db, 1, entity_id=ent_b_khishigdorj.id, role="INVOLVED_IN", note="Хишиг Арвин группийн үүсгэн байгуулагч")
        link_case(db, 1, entity_id=ent_admineral.id, role="BENEFICIARY", note="440 сая ам.долларын нүүрс баяжуулах оффтейк гэрээний тал")
        link_case(db, 1, entity_id=ent_ts_gantulga.id, role="SUSPECT", note="Админерал компанийн захирал, цагдан хоригдсон")
        link_case(db, 1, entity_id=ent_eco_global.id, role="BENEFICIARY", note="Ковидын үеийн нүүрс тээврийн давуу эрхт компани")

        link_case(db, 1, fact_id=f_atut.id, role="EVIDENCE_FOR", note="АТҮТ-ийн 'С' зөвшөөрлийн хууль бус хуваарилалтын баримт")
        link_case(db, 1, fact_id=f_baterdene.id, role="EVIDENCE_FOR", note="Д.Бат-Эрдэнийн бүрэн эрх түдгэлзүүлсэн ялын тогтоол")
        link_case(db, 1, fact_id=f_adshaa.id, role="EVIDENCE_FOR", note="Ш.Адьшаа гишүүний тээврийн компаниудын баримт")
        link_case(db, 1, fact_id=f_khishig_arvin.id, role="EVIDENCE_FOR", note="Хишиг Арвины 1.5 их наядын хөрс хуулалтын баримт")
        link_case(db, 1, fact_id=f_admineral.id, role="EVIDENCE_FOR", note="Админералын 440 сая долларын оффтейк баримт")
        link_case(db, 1, fact_id=f_eco_global.id, role="EVIDENCE_FOR", note="Эко Глобал Ложистикийн монопол тээврийн баримт")

        db.commit()
        print("Нүүрсний 'С' зөвшөөрөл ба Тээврийн компаниудын өгөгдөл амжилттай бүртгэгдлээ!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
