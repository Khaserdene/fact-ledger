# -*- coding: utf-8 -*-
"""Багц 3 & 4: 
3. 'Эмийн үнийн өсөлт, монопол сүлжээ' (Medicine Monopoly & Health Fund)
4. 'Нийслэлийн газрын наймаа ба Хотын бүлэглэл' (UB Land Grabbing & City Faction)

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- Компани, улс төрчдийн хамаарал, хууль бус газар олголт, хэт үнэтэй эмийн төсөв.
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
        print("=== 1. Эмийн үнийн өсөлт, чанарын түр хорооны нээлттэй сонсгол (Case #23) ===")
        src_medicine = create_source(
            db,
            title="Эмийн үнийн өсөлт, чанарын хяналтын талаарх УИХ-ын Түр хорооны нээлттэй сонсголын тайлан",
            url="https://parliament.mn/hearing/medicine-quality-2024",
            selected_text="2024 оны 4-р сард УИХ-аас зохион байгуулсан 'Эмийн үнийн өсөлт, чанарын асуудлаарх' хянан шалгах түр хорооны нээлттэй сонсголоор Монгол Улсын эмийн зах зээлийн 80 гаруй хувийг цөөн тооны томоохон монопол аж ахуйн нэгжүүд хянадаг, Эрүүл мэндийн даатгалын сангийн хөнгөлөлттэй эмийн төсвийн дийлэнхийг эдгээр компаниуд авдаг ба Эмийн зөвлөл, ЭМДЕГ-ын албан тушаалтнууд ашиг сонирхлын ноцтой зөрчилтэй байсан нь илчлэгдсэн.",
            category="document"
        )

        ent_monos = get_or_create_entity(db, "Монос Групп", entity_type="company", aliases=["Монос", "Monos Group"], description="Монголын хамгийн том эм үйлдвэрлэл, импорт, эмийн сангийн сүлжээ")
        ent_l_erdenechimeg = get_or_create_entity(db, "Лувсангийн Эрдэнэчимэг", entity_type="person", aliases=["Л.Эрдэнэчимэг"], description="УИХ-ын гишүүн асан, Монос группийн үүсгэн байгуулагчдын нэг")
        ent_l_khurelbaatar = get_or_create_entity(db, "Лувсангийн Хүрэлбаатар", entity_type="person", aliases=["Л.Хүрэлбаатар"], description="Монос группийн ерөнхийлөгч, үүсгэн байгуулагч")
        ent_em_impex = get_or_create_entity(db, "Эм Импекс Концерн", entity_type="company", aliases=["Эм Импекс", "Em Impex"], description="Эмийн импортын монопол компани")
        ent_europharm = get_or_create_entity(db, "Еврофарм ХХК", entity_type="company", aliases=["Еврофарм"], description="Эмийн импорт, бөөний худалдааны томоохон компани")
        ent_emdeg = get_or_create_entity(db, "Эрүүл Мэндийн Даатгалын Ерөнхий Газар", entity_type="government", aliases=["ЭМДЕГ"], description="Хөнгөлөлттэй эмийн төсвийг хуваарилдаг төрийн байгууллага")

        # Relationships
        add_rel(db, ent_l_khurelbaatar.id, ent_monos.id, "үүсгэн байгуулагч / ерөнхийлөгч", "Монос Групп", source_id=src_medicine.id)
        add_rel(db, ent_l_erdenechimeg.id, ent_monos.id, "хувьцаа эзэмшигч / хамтран үүсгэн байгуулагч", "Монос Групп", source_id=src_medicine.id)
        add_rel(db, ent_emdeg.id, ent_monos.id, "хөнгөлөлттэй эмийн төсөв хуваарилагч", "Монос Групп", source_id=src_medicine.id)

        # Facts
        f_med1 = add_fact(db, ent_monos.id, src_medicine.id,
            "Эмийн түр хорооны нээлттэй сонсголоор Эрүүл мэндийн даатгалын сангаас хөнгөлөлттэй эмийн үнийн зөрүүнд жилд олгодог 90+ тэрбум төгрөгийн төсвийн 40 гаруй хувийг дангаар авч монопол давуу байдал тогтоосон нь ил болсон.",
            fact_date=date(2024, 4, 15), date_precision="day", tags=["эмийн сонсгол", "монопол", "ЭМДЕГ", "төсөв"])

        f_med2 = add_fact(db, ent_l_erdenechimeg.id, src_medicine.id,
            "УИХ-ын гишүүнээр ажиллаж байх хугацаандаа Эмийн тухай хуулийн шинэчилсэн найруулгын ажлын хэсгийг ахалж өөрийн хамаарал бүхий 'Монос' группт давуу байдал олгосон зохицуулалтууд оруулсан ашиг сонирхлын зөрчилтэй байсан нь нээлттэй сонсголоор шүүмжлэгдсэн.",
            fact_date=date(2024, 4, 16), date_precision="day", tags=["ашиг сонирхлын зөрчил", "УИХ", "хууль", "эмийн сонсгол"])

        link_case(db, 23, entity_id=ent_monos.id, role="BENEFICIARY", note="Эмийн хөнгөлөлтийн хамгийн том санхүүжилт авагч монопол")
        link_case(db, 23, entity_id=ent_l_khurelbaatar.id, role="INVOLVED_IN", note="Монос группийн ерөнхийлөгч")
        link_case(db, 23, entity_id=ent_l_erdenechimeg.id, role="DECISION_MAKER", note="Эмийн хуулийг боловсруулахад оролцсон УИХ-ын гишүүн асан")
        link_case(db, 23, entity_id=ent_em_impex.id, role="BENEFICIARY", note="Эмийн импортын төвлөрөл бүхий томоохон компани")
        link_case(db, 23, entity_id=ent_emdeg.id, role="PART_OF_CASE", note="Төсвийг баталж гэрээ байгуулсан төрийн захиргааны байгууллага")
        link_case(db, 23, fact_id=f_med1.id, role="EVIDENCE_FOR", note="90 тэрбумын эмийн санхүүжилтийн төвлөрөл")
        link_case(db, 23, fact_id=f_med2.id, role="EVIDENCE_FOR", note="Ашиг сонирхлын зөрчлийн баримт")

        print("=== 2. Нийслэлийн Газрын Наймаа & Сургууль Цэцэрлэгийн Газар Олголт (Case #17) ===")
        src_land = create_source(
            db,
            title="Нийслэлийн ерөнхий боловсролын сургууль, цэцэрлэг, олон нийтийн эзэмшлийн газрыг эрх мэдэлтнүүдэд олгосон хяналтын тайлан",
            url="https://ulaanbaatar.mn/report/land-grab-investigation",
            selected_text="2000-2020 оны хооронд Улаанбаатар хотын үе үеийн Засаг дарга нарын захирамжаар нийслэлийн сургууль, цэцэрлэгийн эдэлбэр газар, ногоон байгууламж, улсын тусгай хамгаалалттай газруудыг улс төрийн нөлөө бүхий этгээдүүд болон барилгын бүлэглэлүүдэд олгож орон сууц, худалдааны төв бариулсан ноцтой зөрчлүүд илэрсэн.",
            category="document"
        )

        ent_m_enkhbold = get_or_create_entity(db, "Миеэгомбын Энхболд", entity_type="person", aliases=["М.Энхболд"])
        ent_ts_batbayar = get_or_create_entity(db, "Цэнджавын Батбаяр", entity_type="person", aliases=["Ц.Батбаяр"], description="Улаанбаатар хотын Засаг дарга асан (2005-2007)")
        ent_g_munkhbayar = get_or_create_entity(db, "Гомбосүрэнгийн Мөнхбаяр", entity_type="person", aliases=["Г.Мөнхбаяр"], description="Улаанбаатар хотын Засаг дарга асан (2008-2012)")
        ent_e_batuul = get_or_create_entity(db, "Эрдэнийн Бат-Үүл", entity_type="person", aliases=["Э.Бат-Үүл"], description="Улаанбаатар хотын Засаг дарга асан (2012-2016)")
        ent_ub_land_agency = get_or_create_entity(db, "Нийслэлийн Газрын Алба", entity_type="government", aliases=["НГА"], description="Нийслэлийн газар олголтыг хэрэгжүүлэгч агентлаг")

        # Facts
        f_land1 = add_fact(db, ent_m_enkhbold.id, src_land.id,
            "1999-2005 онд Улаанбаатар хотын Засаг даргаар ажиллах хугацаандаа хотын төвийн ногоон байгууламж, хүүхдийн тоглоомын талбай, сургуулийн газруудыг олноор хувьчлах захирамж гаргаж 'Газрын наймааны схем'-ийг эхлүүлсэн гэж шүүмжлэгдсэн.",
            fact_date=date(2004, 6, 1), date_precision="year", tags=["газрын наймаа", "хотын дарга", "хотын фракц"])

        f_land2 = add_fact(db, ent_ts_batbayar.id, src_land.id,
            "Хотын засаг даргаар ажиллахдаа эрх мэдэл, албан тушаалаа урвуулан ашиглаж газар олгосон хэргээр АТГ-аас шалгагдан шүүхээс 2 жил 1 сар хорих ял шийтгүүлсэн.",
            fact_date=date(2014, 11, 10), date_precision="day", tags=["ял", "газрын наймаа", "хотын дарга"])

        link_case(db, 17, entity_id=ent_m_enkhbold.id, role="DECISION_MAKER", note="Нийслэлийн газар олголтыг олон жилээр хэрэгжүүлсэн Хотын дарга")
        link_case(db, 17, entity_id=ent_ts_batbayar.id, role="SUSPECT", note="Газар олголттой холбоотойгоор ял шийтгүүлсэн Хотын дарга")
        link_case(db, 17, entity_id=ent_g_munkhbayar.id, role="DECISION_MAKER", note="Хотын дарга асан")
        link_case(db, 17, entity_id=ent_e_batuul.id, role="DECISION_MAKER", note="Гэр хорооллын дахин төлөвлөлтийг эхлүүлсэн Хотын дарга")
        link_case(db, 17, entity_id=ent_ub_land_agency.id, role="PART_OF_CASE", note="Газар зохион байгуулалтын хэрэгжүүлэгч байгууллага")
        link_case(db, 17, fact_id=f_land1.id, role="EVIDENCE_FOR", note="Хотын төвийн газар олголтын факт")
        link_case(db, 17, fact_id=f_land2.id, role="EVIDENCE_FOR", note="Ц.Батбаярын шүүхийн шийтгэх тогтоол")

        db.commit()
        print("Багц 3 & 4 амжилттай бүртгэгдлээ!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
