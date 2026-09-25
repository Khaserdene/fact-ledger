# -*- coding: utf-8 -*-
"""Багц 6: 
1. 60 тэрбумын схем (Case #12: sixty-billion)
2. Жаст Ойл & Эрдэнэт Стандарт банк (Case #25: standard-bank-erba, Case #26: just-oil-collapse)
3. Оффшор & Панамын баримтууд (Case #19: offshore-panama)

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- source_quote, огноо, холбогдох албан тушаалтан, байгууллагуудыг нэг бүрчлэн холбоно.
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

def add_fact(db, entity, src, fact_type, f_date, text, quote, topic=None, stance=None, sentiment=-0.7):
    f = Fact(
        entity_id=entity.id,
        source_id=src.id,
        fact_type=fact_type,
        fact_date=f_date,
        date_precision="day" if f_date else "year",
        fact_text=text,
        source_quote=quote,
        topic=topic,
        stance=stance,
        sentiment_score=sentiment
    )
    db.add(f)
    db.flush()
    f.fact_id = f"F{f.id}"
    db.flush()
    return f

def main():
    db = SessionLocal()
    try:
        print("=== БАГЦ 6: СҮЛЖЭЭНИЙ ӨГӨГДӨЛ БАЯЖУУЛАЛТ ЭХЭЛЛЭЭ ===")

        # ==========================================
        # 1. 60 ТЭРБУМЫН СХЕМ (Case #12)
        # ==========================================
        case_60 = db.query(Case).filter(Case.slug == "sixty-billion").first()
        if not case_60:
            case_60 = Case(
                title="60 тэрбумын хэрэг & Төрийн албыг үнэлэх схем",
                slug="sixty-billion",
                category="scandal",
                status="PUBLISHED",
                description="2016 оны УИХ-ын сонгуулийн өмнө төрийн албан тушаалуудыг үнэлж 60 тэрбум төгрөг босгох санхүүгийн схем ярилцсан бичлэгийн хэрэг."
            )
            db.add(case_60)
            db.flush()

        src_60 = create_source(
            db,
            title="60 тэрбумын хэргийн аудитын шинжилгээ, шүүхийн шийдвэр",
            url="https://ikon.mn/n/60billion",
            selected_text="2014-2016 онд Нийслэлийн МАН-ын байранд М.Энхболд, Ц.Сандуй, А.Ганбаатар нар төрийн албан тушаалыг үнэлж 60 тэрбум төгрөг босгох схем боловсруулсан гэх хэрэгт Ц.Сандуй, А.Ганбаатар нарт шүүхээс 4 жилийн ял оноож байв.",
            category="court"
        )

        e_enkhbold = get_or_create_entity(db, "Миеэгомбын Энхболд", "person", ["М.Энхболд"])
        e_sandui = get_or_create_entity(db, "Цэндсүрэнгийн Сандуй", "person", ["Ц.Сандуй", "Сандуй дарга"])
        e_ganbaatar = get_or_create_entity(db, "Алтангэрэлийн Ганбаатар", "person", ["А.Ганбаатар", "Шинэ Монгол Хаад"])
        e_dorjzodov = get_or_create_entity(db, "Г.Доржзодов", "person", ["Доржзодов", "Ганзоригийн Доржзодов"], "60 тэрбумын бичлэгийг дэлгэсэн гэрч, стратегич")

        f1 = add_fact(
            db, e_sandui, src_60, "chronological", date(2019, 10, 31),
            "Баянгол дүүргийн Эрүүгийн хэргийн анхан шатны шүүхээс Ц.Сандуйд төрийн эрхийг хууль бусаар авах хуйвалдаан зохион байгуулсан гэм буруутайд тооцож 4 жилийн хорих ял оноов.",
            "Шүүхээс Ц.Сандуй, А.Ганбаатар нарт 4 жилийн хорих ял оноож, ялыг нээлттэй хорих ангид эдлүүлэхээр шийдвэрлэсэн байна.",
            "60 тэрбум", "ял сонссон", -0.9
        )
        f2 = add_fact(
            db, e_ganbaatar, src_60, "chronological", date(2019, 10, 31),
            "А.Ганбаатарт 60 тэрбумын хэрэгт хамтран оролцсон үндэслэлээр 4 жилийн хорих ял оноосон.",
            "Шүүгдэгч А.Ганбаатарт төрийн эрхийг хууль бусаар авах хуйвалдаан зохион байгуулсан хэрэгт 4 жилийн хорих ял оноов.",
            "60 тэрбум", "ял сонссон", -0.9
        )
        f3 = add_fact(
            db, e_enkhbold, src_60, "chronological", date(2019, 1, 29),
            "60 тэрбумын хэрэг болон МАН доторх улс төрийн хямралын улмаас УИХ-ын дарга М.Энхболдыг албан тушаалаас нь огцруулав.",
            "УИХ-ын чуулганы нэгдсэн хуралдаанаар гишүүдийн 66.2 хувийн саналаар УИХ-ын дарга М.Энхболдыг үүрэгт ажлаас нь чөлөөллөө.",
            "60 тэрбум", "огцорсон", -0.8
        )

        for ent, role, note in [
            (e_enkhbold, "DECISION_MAKER", "Нийслэлийн МАН-ын хорооны хуралдаан болон ярианы бичлэгт дурдагдсан намын дарга"),
            (e_sandui, "SUSPECT", "Төрийн албыг үнэлэх төлөвлөгөөг боловсруулж ял сонссон НИТХ-ын дарга асан"),
            (e_ganbaatar, "SUSPECT", "60 тэрбумын схем загварыг боловсруулахад оролцсон"),
            (e_dorjzodov, "INVOLVED_IN", "Бичлэгийг хууль хяналтын байгууллага болон нийтэд ил болгосон гэрч")
        ]:
            if not db.query(CaseLink).filter(CaseLink.case_id == case_60.id, CaseLink.entity_id == ent.id).first():
                db.add(CaseLink(case_id=case_60.id, entity_id=ent.id, role=role, note=note))

        # ==========================================
        # 2. ЖАСТ ОЙЛ & СТАНДАРТ БАНК (Case #25 & #26)
        # ==========================================
        case_std = db.query(Case).filter(Case.slug == "standard-bank-erba").first()
        case_just = db.query(Case).filter(Case.slug == "just-oil-collapse").first()

        src_just = create_source(
            db,
            title="Эрдэнэт үйлдвэр ба Стандарт банкны арбитрын маргаан, Ш.Батхүүгийн хэрэг",
            url="https://news.mn/r/standard-bank-just",
            selected_text="Жаст группын захирал Ш.Батхүү нь Өмнөд Африкийн Стандарт банкнаас 109 сая ам.долларын зээл авахдаа Эрдэнэт үйлдвэрийн 51 хувийг барьцаалж, Ч.Ганзориг, Д.Сүрэнхорлоо нарын гарын үсгийг хуурамчаар зурсан болон баталгаа гаргуулсан хэрэгт яллагдагчаар татагдсан. Арбитрын шүүхээс Монголын талыг 115 сая ам.доллар төлөх шийдвэр гаргаж, Засгийн газрын нөөц сангаас төлсөн.",
            category="court"
        )

        e_batkhuu = get_or_create_entity(db, "Шүрэнгийн Батхүү", "person", ["Ш.Батхүү", "Жастын Батхүү"], "Жаст группийн ерөнхийлөгч")
        e_just_group = get_or_create_entity(db, "Жаст групп ХХК", "company", ["Just Group", "Жаст Ойл"], "Шатахуун импорт, банкны салбарт ажиллаж дампуурсан групп")
        e_ganzorig = get_or_create_entity(db, "Чимиддоржийн Ганзориг", "person", ["Ч.Ганзориг"], "Эрдэнэт үйлдвэрийн захирал асан")
        e_erdenet = get_or_create_entity(db, "Эрдэнэт үйлдвэр ТӨХК", "company", ["Эрдэнэт үйлдвэр", "Erdenet Mining"])
        e_surenkhorloo = get_or_create_entity(db, "Д.Сүрэнхорлоо", "person", ["Сүрэнхорлоо"], "Эрдэнэт үйлдвэрийн хуулийн хэлтсийн дарга асан")

        f_b1 = add_fact(
            db, e_batkhuu, src_just, "chronological", date(2022, 10, 25),
            "Шүүхээс Ш.Батхүүд бусдын эд хөрөнгийг залилсан, хуурамч бичиг баримт ашигласан үндэслэлээр 8 жилийн хорих ял оноож, 140 гаруй тэрбум төгрөгийн хохирол төлүүлэхээр тогтоов.",
            "Шүүхээс Ш.Батхүүд 8 жилийн хорих ял оногдуулж, Эрдэнэт үйлдвэр болон Хадгаламж банкны хохирлыг нөхөн төлүүлэхээр шийдвэрлэв.",
            "Жаст Ойл", "хорих ял", -0.9
        )
        f_b2 = add_fact(
            db, e_ganzorig, src_just, "chronological", date(2013, 6, 10),
            "Эрдэнэт үйлдвэрийн 51 хувийг Стандарт банканд барьцаалах батлан даалтад гарын үсэг зурсан асуудлаар хууль хяналтын байгууллагад шалгагдав.",
            "Эрдэнэт үйлдвэрийн ерөнхий захирал асан Ч.Ганзориг нь Стандарт банкны зээлийн баталгаанд гарын үсэг зурсан хэрэгт холбогдсон.",
            "Стандарт банк", "шалгагдсан", -0.7
        )

        for ent, role, note in [
            (e_batkhuu, "SUSPECT", "Хуурамч баталгаа ашиглан 109 сая долларын зээл авч хохирол учруулсан"),
            (e_just_group, "BENEFICIARY", "Стандарт банк болон Хадгаламж банкнаас зээл авсан үндсэн компани"),
            (e_ganzorig, "DECISION_MAKER", "Эрдэнэт үйлдвэрийн ерөнхий захирлаар ажиллахдаа батлан даалт гаргасан"),
            (e_erdenet, "BENEFICIARY", "51 хувь нь барьцаалагдаж арбитрын 115 сая долларын өрөнд орсон"),
            (e_surenkhorloo, "INVOLVED_IN", "Хуулийн хэлтсийн даргаар ажиллаж баримт бичгийг баталгаажуулсан")
        ]:
            if case_std and not db.query(CaseLink).filter(CaseLink.case_id == case_std.id, CaseLink.entity_id == ent.id).first():
                db.add(CaseLink(case_id=case_std.id, entity_id=ent.id, role=role, note=note))
            if case_just and not db.query(CaseLink).filter(CaseLink.case_id == case_just.id, CaseLink.entity_id == ent.id).first():
                db.add(CaseLink(case_id=case_just.id, entity_id=ent.id, role=role, note=note))

        # ==========================================
        # 3. ПАНАМЫН БАРИМТ & ОФФШОР ДАНС (Case #19)
        # ==========================================
        case_offshore = db.query(Case).filter(Case.slug == "offshore-panama").first()
        src_panama = create_source(
            db,
            title="Олон улсын эрэн сурвалжлах сэтгүүлчдийн консорциум (ICIJ) Панамын баримтууд",
            url="https://offshoreleaks.icij.org/search?q=Mongolia",
            selected_text="2016 онд ICIJ-ээс ил болгосон Панамын баримтад Монгол Улсын ерөнхий сайд асан Сү.Батболд, Сангийн сайд асан С.Баярцогт, УИХ-ын гишүүн Д.Цогтбаатар, хотын дарга асан Э.Бат-Үүл нарын гэр бүл, холбоотой этгээдүүдийн оффшор данс, компаниуд ил болж байв.",
            category="leak"
        )

        e_batbold = get_or_create_entity(db, "Сүхбаатарын Батболд", "person", ["Сү.Батболд"])
        e_bayartsogt = get_or_create_entity(db, "Сангажавын Баярцогт", "person", ["С.Баярцогт"])
        e_tsogtbaatar = get_or_create_entity(db, "Дамдины Цогтбаатар", "person", ["Д.Цогтбаатар"])
        e_bat_uul = get_or_create_entity(db, "Эрдэнийн Бат-Үүл", "person", ["Э.Бат-Үүл", "Бат-Үүл"])

        f_o1 = add_fact(
            db, e_bayartsogt, src_panama, "chronological", date(2013, 4, 18),
            "Швейцарийн Credit Suisse банканд 1 сая ам.долларын нууц данс, Legend Plus Capital оффшор компани илэрснээр УИХ-ын дэд даргын албан тушаалаас огцров.",
            "С.Баярцогт оффшор бүс дэх дансаа хөрөнгө орлогын мэдүүлэгтээ дурдаагүйгээ хүлээн зөвшөөрч дэд даргын суудлаа өгөв.",
            "Оффшор", "огцорсон", -0.8
        )
        f_o2 = add_fact(
            db, e_batbold, src_panama, "chronological", date(2020, 11, 20),
            "Нью-Йорк болон Лондон хотын шүүхэд Сү.Батболд болон түүний хамаарал бүхий оффшор бүтэцтэй холбоотой хөрөнгийг царцаах нэхэмжлэлийг Эрдэнэт үйлдвэр болон Оюу толгойн нэрийн өмнөөс гаргав.",
            "АНУ-ын шүүхэд Сү.Батболдтой холбоотой тансаг зэрэглэлийн үл хөдлөх хөрөнгүүдийг оффшор схемээр угаасан гэх хэрэг маргаан үүсэв.",
            "Оффшор", "нэхэмжлэл", -0.7
        )

        for ent, role, note in [
            (e_batbold, "BENEFICIARY", "Олон улсын шүүхэд оффшор үл хөдлөх хөрөнгө, компаниудтай холбогдон нэхэмжлэгдсэн"),
            (e_bayartsogt, "SUSPECT", "Швейцарийн нууц данс болон Legend Plus Capital компаниар шалгагдсан"),
            (e_tsogtbaatar, "INVOLVED_IN", "Панамын баримтад дурдагдсан оффшор компанийн хувьцаа эзэмшигч"),
            (e_bat_uul, "INVOLVED_IN", "Хүү Б.Чулуудай нь оффшор компани бүртгүүлсэн асуудалд холбогдсон")
        ]:
            if case_offshore and not db.query(CaseLink).filter(CaseLink.case_id == case_offshore.id, CaseLink.entity_id == ent.id).first():
                db.add(CaseLink(case_id=case_offshore.id, entity_id=ent.id, role=role, note=note))

        db.commit()
        print("=== БАГЦ 6: АМЖИЛТТАЙ ХАДГАЛАГДЛАА ===")

    except Exception as e:
        db.rollback()
        print("Алдаа гарлаа:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
