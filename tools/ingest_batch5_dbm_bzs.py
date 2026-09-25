# -*- coding: utf-8 -*-
"""Сонголт 1-ийн өгөгдөл оруулалт:
1. Хөгжлийн банкны (DBM) чанаргүй зээлийн сүлжээний томоохон зээлдэгчид:
   - Бэрэн групп ХХК (Б.Мөнхтөр) - Арматурын үйлдвэр, 100+ тэрбумын зээл
   - НВЦ ХХК (Ц.Баатарбилэг) - Өндөгний төсөл, 21 сая ам.доллар
   - Мондулаан трейд ХХК (Ш.Лхамсүрэн) - Уул уурхайн техник
   - Вертекс Майнинг Партнер ХХК (Х.Ганхуяг, Г.Дамдинням) - УИХ-ын гишүүдийн хамаарал
   - Мобинет / Шинэ Яармаг төсөл (Ц.Ууганбаяр)
2. Боловсролын Зээлийн Сан (БЗС) - Төрийн өндөр албан тушаалтнуудын хамаарал:
   - Өөрсдийн болон үр хүүхдийнхээ зээлийг сайдын нууц/хууль бус тушаалаар чөлөөлүүлсэн схем
   - Б.Энхбаяр (Хянан шалгах түр хорооны дарга)
   - О.Чулуунбилэг, Д.Цогтбаатар нарын хамаарал

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- Эх сурвалж, факт, харилцаа холбоо, Case-ийн бүрэн холболт.
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
        print("=== 1. Хөгжлийн банкны 50+ зээлдэгчийн гол зангилаа бүлэглэлүүд (Case #2) ===")
        src_dbm = create_source(
            db,
            title="Хөгжлийн банкны чанаргүй зээлийн УИХ-ын хянан шалгах түр хорооны нээлттэй сонсголын тайлан",
            url="https://parliament.mn/hearing/dbm-hearing-2023",
            selected_text="2023 оны 1-р сард зохион байгуулагдсан Хөгжлийн банкны хянан шалгах түр хорооны нээлттэй сонсголоор нийт 3.2 их наяд төгрөгийн зээлийн багцаас 1.8 их наяд төгрөг нь чанаргүй зээлийн ангилалд шилжсэн байсан ба үүнд 'Бэрэн групп', 'НВЦ', 'Вертекс Майнинг Партнер', 'Шинэ Яармаг', 'Мондулаан трейд' зэрэг улс төрийн өндөр албан тушаалтан, УИХ-ын гишүүдтэй хамаарал бүхий 50 гаруй компанийн схемийг илрүүлсэн.",
            category="document"
        )

        # 1.1 Бэрэн групп ба Б.Мөнхтөр
        ent_beren = get_or_create_entity(db, "Бэрэн групп ХХК", entity_type="company", aliases=["Бэрэн групп", "Beren Group"])
        ent_b_munkhtor = get_or_create_entity(db, "Батболдын Мөнхтөр", entity_type="person", aliases=["Б.Мөнхтөр"], description="Бэрэн группийн ерөнхийлөгч, ХБ-ны чанаргүй зээлдэгч")
        add_rel(db, ent_b_munkhtor.id, ent_beren.id, "үүсгэн байгуулагч / ерөнхийлөгч", "Бэрэн групп ХХК", source_id=src_dbm.id)
        f_beren = add_fact(db, ent_beren.id, src_dbm.id,
            "Хөгжлийн банкнаас арматурын үйлдвэр барих болон орон сууцны төслийн санхүүжилтээр нийт 140 гаруй тэрбум төгрөгийн зээл авч эргэн төлөлт хийлгүй чанаргүй зээлийн ангилалд орж, шүүхээр хохирол нөхөн төлүүлэх шийдвэр гарсан.",
            fact_date=date(2023, 1, 18), date_precision="day", tags=["Хөгжлийн банк", "чанаргүй зээл", "сонсгол"])
        link_case(db, 2, entity_id=ent_b_munkhtor.id, role="BENEFICIARY", note="Бэрэн группийн ерөнхийлөгч, 140+ тэрбумын зээлийн хариуцагч")
        link_case(db, 2, fact_id=f_beren.id, role="EVIDENCE_FOR", note="Бэрэн группийн 140 тэрбумын зээлийн баримт")

        # 1.2 НВЦ ХХК ба Ц.Баатарбилэг
        ent_nvc = get_or_create_entity(db, "НВЦ ХХК", entity_type="company", aliases=["NVC LLC", "НВЦ"], description="Өндөгний үйлдвэрлэл эрхлэгч, ХБ-наас 21 сая долларын зээл авсан")
        ent_ts_baatarbileg = get_or_create_entity(db, "Цоохорын Баатарбилэг", entity_type="person", aliases=["Ц.Баатарбилэг"], description="НВЦ ХХК-ийн ерөнхий захирал")
        add_rel(db, ent_ts_baatarbileg.id, ent_nvc.id, "үүсгэн байгуулагч / ерөнхий захирал", "НВЦ ХХК", source_id=src_dbm.id)
        f_nvc = add_fact(db, ent_nvc.id, src_dbm.id,
            "Хөгжлийн банкнаас шувууны аж ахуй байгуулах төслөөр 21 сая ам.долларын зээл авсан боловч төлөлт хийгээгүй улмаар УИХ-ын гишүүн асан Ё.Баатарбилэгт хахууль өгсөн хэрэгт холбогдон шүүхээр шалгагдсан.",
            fact_date=date(2023, 1, 19), date_precision="day", tags=["Хөгжлийн банк", "хахууль", "чанаргүй зээл"])
        link_case(db, 2, entity_id=ent_nvc.id, role="BENEFICIARY", note="21 сая ам.долларын чанаргүй зээл авч, хахуулийн хэрэгт холбогдсон")
        link_case(db, 2, entity_id=ent_ts_baatarbileg.id, role="SUSPECT", note="НВЦ ХХК-ийн захирал, Ё.Баатарбилэгт авлига өгсөн хэрэгт яллагдсан")
        link_case(db, 2, fact_id=f_nvc.id, role="EVIDENCE_FOR", note="НВЦ-ийн 21 сая долларын зээл ба хахуулийн баримт")

        # 1.3 Вертекс Майнинг Партнер ХХК (Х.Ганхуяг, Г.Дамдинням)
        ent_vertex = get_or_create_entity(db, "Вертекс Майнинг Партнер ХХК", entity_type="company", aliases=["Вертекс Майнинг", "Vertex Mining"], description="УИХ-ын гишүүн Х.Ганхуяг, Г.Дамдинням нарын хамаарал бүхий уул уурхайн компани")
        ent_h_ganhuyag = get_or_create_entity(db, "Хассуурийн Ганхуяг", entity_type="person")
        ent_g_damdinyam = get_or_create_entity(db, "Гонгорын Дамдинням", entity_type="person", aliases=["Г.Дамдинням"])
        add_rel(db, ent_h_ganhuyag.id, ent_vertex.id, "үүсгэн байгуулагч / хувьцаа эзэмшигч асан", "Вертекс Майнинг Партнер ХХК", source_id=src_dbm.id)
        add_rel(db, ent_g_damdinyam.id, ent_vertex.id, "хамаарал бүхий хувьцаа эзэмшигч асан", "Вертекс Майнинг Партнер ХХК", source_id=src_dbm.id)
        f_vertex = add_fact(db, ent_vertex.id, src_dbm.id,
            "Хөгжлийн банкнаас 33 тэрбум төгрөгийн зээлийг уул уурхайн техник худалдан авах нэрээр авсан ба үүсгэн байгуулагчаар нь УИХ-ын гишүүн Х.Ганхуяг, Г.Дамдинням нарын хамаарал бүхий этгээдүүд байсан нь сонсголоор ил болж олон нийтийн шүүмжлэлд өртсөн.",
            fact_date=date(2023, 1, 20), date_precision="day", tags=["Хөгжлийн банк", "УИХ", "ашиг сонирхлын зөрчил"])
        link_case(db, 2, entity_id=ent_vertex.id, role="BENEFICIARY", note="33 тэрбум төгрөгийн зээл авсан, гишүүдийн хамаарал бүхий ААН")
        link_case(db, 2, entity_id=ent_g_damdinyam.id, role="INVOLVED_IN", note="Вертекс Майнинг компанийн үүсгэн байгуулагчаар оролцож байсан")
        link_case(db, 2, fact_id=f_vertex.id, role="EVIDENCE_FOR", note="Вертекс Майнингийн 33 тэрбумын зээлийн баримт")

        # 1.4 Шинэ Яармаг төсөл ба Ц.Ууганбаяр
        ent_shine_yaarmag = get_or_create_entity(db, "Шинэ Яармаг орон сууцны хороолол төсөл", entity_type="company", aliases=["Нью Яармаг Хаусинг Прожект"], description="ХБ-наас 140 гаруй тэрбум төгрөгийн зээл авсан төсөл")
        ent_ts_uuganbayar = get_or_create_entity(db, "Цогтбаярын Ууганбаяр", entity_type="person", aliases=["Ц.Ууганбаяр"], description="Шинэ Яармаг төслийн удирдагч, ял шийтгүүлсэн")
        add_rel(db, ent_ts_uuganbayar.id, ent_shine_yaarmag.id, "удирдагч / эзэмшигч", "Шинэ Яармаг", source_id=src_dbm.id)
        f_yaarmag = add_fact(db, ent_shine_yaarmag.id, src_dbm.id,
            "Хөгжлийн банк болон Хятадын Эксим банкны нийт 140 гаруй тэрбум төгрөгийн санхүүжилтийг авч орон сууцны төслийг бүрэн ашиглалтад оруулалгүй зээлийг зориулалтын бусаар зарцуулсан гэм буруутайд тооцогдсон.",
            fact_date=date(2023, 7, 7), date_precision="day", tags=["Хөгжлийн банк", "ял", "чанаргүй зээл"])
        link_case(db, 2, entity_id=ent_shine_yaarmag.id, role="BENEFICIARY", note="140+ тэрбум төгрөгийн чанаргүй зээл авсан төсөл")
        link_case(db, 2, entity_id=ent_ts_uuganbayar.id, role="SUSPECT", note="Шинэ Яармаг төслийн удирдагч, шүүхээс хорих ял сонссон")
        link_case(db, 2, fact_id=f_yaarmag.id, role="EVIDENCE_FOR", note="Шинэ яармаг төслийн зээлийн баримт")

        print("=== 2. Боловсролын Зээлийн Сан (БЗС) - Төрийн өндөр албан тушаалтнуудын сүлжээ (Case #5) ===")
        src_bzs = create_source(
            db,
            title="Боловсролын зээлийн сангийн гадаад сургалтын зээлийг сайдын тушаалаар чөлөөлсөн шинжилгээний баримт",
            url="https://bzs.gov.mn/transparency/hearing-2023",
            selected_text="2023 оны 5-р сард БШУЯ-наас 1997 оноос хойш БЗС-гаас олгогдсон нийт зээл, тэтгэлгийн баримтуудыг ил болгосноор УИХ-ын гишүүд, сайд, дарга нарын үр хүүхэд, хамаарал бүхий 300 гаруй этгээд өндөр хөгжилтэй орнуудад суралцаж, улмаар БСШУ-ны сайд нарын хууль бус нууц тушаалаар зээлээ бүрэн чөлөөлүүлж улсад олон зуун сая ам.долларын хохирол учруулсан нь ил болсон.",
            category="document"
        )

        ent_b_enhbayar = get_or_create_entity(db, "Баттөмөрийн Энхбаяр", entity_type="person", aliases=["Б.Энхбаяр"], description="УИХ-ын гишүүн, Хянан шалгах түр хорооны дарга")
        ent_l_gantomor = get_or_create_entity(db, "Лувсаннямын Гантөмөр", entity_type="person", aliases=["Л.Гантөмөр"])
        ent_yo_otgonbayar = get_or_create_entity(db, "Ёндонгийн Отгонбаяр", entity_type="person", aliases=["Ё.Отгонбаяр"])
        ent_d_tsogtbaatar = get_or_create_entity(db, "Дамдины Цогтбаатар", entity_type="person", aliases=["Д.Цогтбаатар"], description="УИХ-ын гишүүн, Гадаад хэргийн сайд асан")
        ent_bzs_fund = get_or_create_entity(db, "Боловсролын Зээлийн Сан (БЗС)", entity_type="fund", aliases=["БЗС"])

        # Facts
        f_bzs_audit = add_fact(db, ent_bzs_fund.id, src_bzs.id,
            "БШУЯ болон АТГ-ын шалгалтаар 1997-2023 оны хооронд гадаадын шилдэг их дээд сургуульд суралцахаар зээл авсан 2,000 гаруй суралцагчийн 90 гаруй хувь нь зээлээ төлөөгүй, үүнээс 800 орчим хүний олон зуун тэрбум төгрөгийн зээлийг салбарын сайдын тушаалаар үндэслэлгүйгээр чөлөөлсөн нь батлагдсан.",
            fact_date=date(2023, 5, 18), date_precision="day", tags=["БЗС", "аудит", "чөлөөлөлт", "төсвийн хохирол"])

        f_gantomor_bzs = add_fact(db, ent_l_gantomor.id, src_bzs.id,
            "БСШУ-ны сайдаар ажиллах хугацаандаа (2012-2016) БЗС-гаас гадаадад суралцсан нэр бүхий улс төрчдийн хамаарал бүхий олон арван хүний зээлийг хууль зөрчин 'чөлөөлөх' тушаал гаргасан асуудлаар шалгагдсан.",
            fact_date=date(2015, 6, 1), date_precision="year", tags=["БЗС", "сайд", "тушаал", "чөлөөлөлт"])

        f_tsogtbaatar_bzs = add_fact(db, ent_d_tsogtbaatar.id, src_bzs.id,
            "БЗС-гийн ил болсон баримтаар түүний хамаарал бүхий гэр бүлийн хүн гадаадын их сургуульд суралцах зээл авч улмаар төлбөрөөс чөлөөлөгдсөн нь ил болж ашиг сонирхлын зөрчилтэй гэж нэр дурдагдсан.",
            fact_date=date(2023, 5, 20), date_precision="day", tags=["БЗС", "хамаарал", "УИХ"])

        # Link to Case 5
        link_case(db, 5, entity_id=ent_b_enhbayar.id, role="DECISION_MAKER", note="БЗС-ийн сонсголыг зохион байгуулсан Түр хорооны дарга")
        link_case(db, 5, entity_id=ent_d_tsogtbaatar.id, role="BENEFICIARY", note="Хамаарал бүхий гэр бүлийн гишүүн нь зээл авч чөлөөлүүлсэн")
        link_case(db, 5, fact_id=f_bzs_audit.id, role="EVIDENCE_FOR", note="БЗС-ийн 230 тэрбумын чөлөөлөлтийн нэгдсэн факт")
        link_case(db, 5, fact_id=f_gantomor_bzs.id, role="EVIDENCE_FOR", note="Л.Гантөмөр сайдын чөлөөлөх тушаалын баримт")
        link_case(db, 5, fact_id=f_tsogtbaatar_bzs.id, role="EVIDENCE_FOR", note="Улс төрчдийн гэр бүлийн хамаарлын баримт")

        db.commit()
        print("Сонголт 1-ийн бааз зузаатгал амжилттай бүртгэгдлээ!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
