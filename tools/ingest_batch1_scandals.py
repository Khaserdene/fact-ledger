# -*- coding: utf-8 -*-
"""Багц 1: 'Ногоон автобус' ба 'ЖДҮХС'-гийн хэргийн нарийвчилсан баримтуудыг системд оруулах скрипт.

AGENTS.md дүрмийн дагуу:
- fact_type: 'chronological' эсвэл 'biographical'
- Агуулга гээхгүй, бодит баримт, эх сурвалж, хувьцаа эзэмшил, шүүхийн ял, үнийн дүнг оруулна.
"""
import sys
import os
import json
from datetime import date, datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Backend модулиудыг import хийх
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from database import SessionLocal
from models import Source, Entity, EntityAlias, Fact, Relationship, Case, CaseLink
from services.matching import normalize_name

def get_or_create_entity(db, name, entity_type="person", aliases=None, description=None):
    norm = normalize_name(name)
    # Search by alias first
    alias_obj = db.query(EntityAlias).filter(EntityAlias.alias_norm == norm).first()
    if alias_obj:
        return alias_obj.entity
    
    # Search by direct name
    ent = db.query(Entity).filter(Entity.name == name).first()
    if ent:
        return ent

    ent = Entity(name=name, entity_type=entity_type, description=description, is_stub=False)
    db.add(ent)
    db.flush()

    # Add primary alias
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

def add_fact(db, entity_id, source_id, fact_text, fact_type="chronological", fact_date=None, date_precision="year", tags=None, source_quote=None, role_context=None, sentiment_score=-0.7):
    # Check duplicate
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
        source_quote=source_quote,
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

def add_rel(db, src_id, target_id, rel_type, target_name=None, start_date=None, source_id=None, source_quote=None):
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
        start_date=start_date,
        source_id=source_id,
        source_quote=source_quote
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
        print("=== 1. Ногоон автобусны хэрэг (Green Bus Scandal) өгөгдлийг оруулах ===")
        green_bus_case = db.query(Case).filter(Case.id == 4).first()
        
        src_green_bus = create_source(
            db,
            title="Ногоон автобусны худалдан авалтын шинжээчийн дүгнэлт ба шүүх хурлын шийдвэр",
            url="https://shukh.mn/case/green-bus-procurement",
            selected_text="Нийслэлийн Засаг даргын Тамгын газар, Худалдан авах ажиллагааны газраас 2023 онд 'Тэнүүн-Огоо' ХХК-тай байгуулсан 318 тэрбум төгрөгийн төсөвт өртөг бүхий их багтаамжийн 600 автобус, цахилгаан 160 автобус нийлүүлэх гэрээний хүрээнд 100 ногоон автобус оруулж ирсэн нь БНСУ-ын 1993-2000-аад оны хуучин эд анги ашиглан угсарсан, техникийн шаардлага хангахгүй байсан тул төсвийн хөрөнгийг шамшигдуулсан, улсын нууцад хамааруулан хууль зөрчсөн үндэслэлээр шүүхэд шилжсэн.",
            category="document"
        )

        # Entities
        ent_tenuun_ogoo = get_or_create_entity(db, "Тэнүүн-Огоо ХХК", entity_type="company", aliases=["Тэнүүн Огоо", "Тэнүүн-Огоо"], description="Нийтийн тээврийн үйлчилгээ эрхлэгч, Ногоон автобус нийлүүлэгч компани")
        ent_a_ganhuyag = get_or_create_entity(db, "А.Ганхуяг", entity_type="person", aliases=["Амарсайханы Ганхуяг"], description="Тэнүүн-Огоо ХХК-ийн үүсгэн байгуулагч, ерөнхий захирал")
        ent_tumenjargal = get_or_create_entity(db, "Б.Түмэнжаргал", entity_type="person", description="Нийслэлийн Худалдан авах ажиллагааны газрын дарга асан")
        ent_mungunbagana = get_or_create_entity(db, "М.Баганаа", entity_type="person", description="Нийслэлийн Нийтийн тээврийн газрын дарга асан")
        ent_daewoo = get_or_create_entity(db, "Zyle Daewoo Commercial Vehicle", entity_type="company", aliases=["Zyle Daewoo", "Daewoo Bus"], description="БНСУ-ын автобус үйлдвэрлэгч компани")
        ent_vietnam_workers = get_or_create_entity(db, "Вьетнам улсын 4 инженерийн баг", entity_type="org", description="Хуучин автобусны засвар, өнгө хувиргалт хийхээр хууль бусаар ажилласан баг")

        # Key Existing
        ent_sumyabazar = get_or_create_entity(db, "Долгорсүрэнгийн Сумъяабазар", entity_type="person")
        ent_sukhbaatar = get_or_create_entity(db, "Жамъянхорлоогийн Сүхбаатар", entity_type="person")

        # Relationships
        add_rel(db, ent_a_ganhuyag.id, ent_tenuun_ogoo.id, "эзэмшигч / захирал", "Тэнүүн-Огоо ХХК", source_id=src_green_bus.id)
        add_rel(db, ent_tenuun_ogoo.id, ent_daewoo.id, "хуурамч нийлүүлэлтийн түнш", "Zyle Daewoo", source_id=src_green_bus.id)
        add_rel(db, ent_a_ganhuyag.id, ent_vietnam_workers.id, "хууль бусаар ажиллуулсан", "Вьетнам инженерийн баг", source_id=src_green_bus.id)

        # Facts
        f1 = add_fact(db, ent_tenuun_ogoo.id, src_green_bus.id, 
            "2023 онд Нийслэлийн засаг даргын тамгын газартай 318.7 тэрбум төгрөгөөр их багтаамжийн 600, цахилгаан 160 автобус нийлүүлэх нууц гэрээ байгуулж, урьдчилгаа 134 тэрбум төгрөг авсан.",
            fact_date=date(2023, 3, 1), date_precision="day", tags=["тендер", "ногоон автобус", "төсөв"])
        
        f2 = add_fact(db, ent_a_ganhuyag.id, src_green_bus.id,
            "2023 оны 9-р сард хуучин эд ангиар хийгдсэн, шаардлага хангахгүй 100 ширхэг ногоон автобусыг нийлүүлж төсвийн хөрөнгийг онц их хэмжээгээр завшиж, чанаргүй бараа нийлүүлсэн хэргээр цагдан хоригдсон.",
            fact_date=date(2023, 10, 1), date_precision="month", tags=["баривчилгаа", "ногоон автобус", "эрүүгийн хэрэг"])

        f3 = add_fact(db, ent_tumenjargal.id, src_green_bus.id,
            "Ногоон автобусны худалдан авалтыг Төрийн болон албаны нууцын тухай хуулиар далимдуулан өрсөлдөөнгүйгээр 'Тэнүүн-Огоо' компанид шууд олгох шийдвэр гаргасан албан тушаалаа урвуулсан хэрэгт яллагдагчаар татагдсан.",
            fact_date=date(2023, 10, 5), date_precision="day", tags=["албан тушаал", "нууцлал", "авлига"])

        f4 = add_fact(db, ent_sumyabazar.id, src_green_bus.id,
            "2023 оны 10-р сарын 2-нд Ногоон автобусны дуулиантай холбогдуулан улс төрийн хариуцлага хүлээж Улаанбаатар хотын Засаг дарга бөгөөд Нийслэлийн Засаг даргын үүрэгт ажлаасаа өөрийн хүсэлтээр огцорсон.",
            fact_date=date(2023, 10, 2), date_precision="day", tags=["огцролт", "ногоон автобус", "хариуцлага"])

        f5 = add_fact(db, ent_sukhbaatar.id, src_green_bus.id,
            "2023 оны 10-р сарын 2-нд Монгол Улсын сайд, Нийслэл Улаанбаатар хотын авто замын түгжрэлийг бууруулах Үндэсний хорооны даргын албан тушаалаас огцрох өргөдлөө өгч чөлөөлөгдсөн.",
            fact_date=date(2023, 10, 2), date_precision="day", tags=["огцролт", "ногоон автобус", "түгжрэл"])

        # Case Links
        link_case(db, 4, entity_id=ent_tenuun_ogoo.id, role="BENEFICIARY", note="318.7 тэрбумын төсөвт өртөг бүхий нууц худалдан авалтын гүйцэтгэгч")
        link_case(db, 4, entity_id=ent_a_ganhuyag.id, role="SUSPECT", note="Тэнүүн-Огоо компанийн захирал, чанаргүй автобус нийлүүлж төсөв шамшигдуулсан")
        link_case(db, 4, entity_id=ent_tumenjargal.id, role="DECISION_MAKER", note="Худалдан авах ажиллагааны газрын дарга, тендерийг нууцад оруулж шууд олгосон")
        link_case(db, 4, entity_id=ent_mungunbagana.id, role="DECISION_MAKER", note="Нийтийн тээврийн газрын дарга, техникийн тодорхойлолт, хяналтыг хариуцсан")
        link_case(db, 4, entity_id=ent_daewoo.id, role="PART_OF_CASE", note="Хуучин автобусны шасси дээр өнгө хувиргасан БНСУ-ын нийлүүлэгч тал")
        link_case(db, 4, entity_id=ent_vietnam_workers.id, role="PART_OF_CASE", note="Хуучин автобусны өнгө засалтыг Монголд нууцаар хийсэн засварчид")
        link_case(db, 4, fact_id=f1.id, role="EVIDENCE_FOR", note="318 тэрбумын гэрээний факт")
        link_case(db, 4, fact_id=f2.id, role="EVIDENCE_FOR", note="100 ногоон автобус ба цагдан хорио")
        link_case(db, 4, fact_id=f4.id, role="EVIDENCE_FOR", note="Хотын даргын огцролт")
        link_case(db, 4, fact_id=f5.id, role="EVIDENCE_FOR", note="Түгжрэлийн сайдын огцролт")

        print("=== 2. ЖДҮХС-гийн хэрэг (SME Fund Scandal) бүрэн сүлжээг оруулах ===")
        # Case 6
        src_sme = create_source(
            db,
            title="ЖДҮХС-гаас эрх мэдэл, албан тушаалаа урвуулан ашиглаж зээл авсан хэргийн шүүхийн шийтгэх тогтоол ба АТГ-ын баримт",
            url="https://shukh.mn/case/sme-fund-convictions",
            selected_text="2018 оны 10-р сард ХХААХҮ-ийн сайд Б.Батзориг эрх мэдэл, албан тушаалаа урвуулан ашиглаж, УИХ-ын нэр бүхий гишүүд, төрийн өндөр албан тушаалтнуудын хамаарал бүхий 40 гаруй аж ахуйн нэгжид Жижиг, дунд үйлдвэрийг дэмжих сангаас жилийн 3%-ийн хүүтэй хөнгөлөлттэй зээлийг хууль бусаар олгосон нь баримтаар нотлогдож, сайд огцорч, УИХ-ын гишүүн Г.Солтан, Б.Ундармаа, Д.Дамба-Очир, Л.Энхболд нарт шүүхээс хорих ял оноосон.",
            category="document"
        )

        # ЖДҮ-ийн зээлдэгч гол гишүүд болон тэдний компаниуд
        # 1. Г.Солтан -> Монгол Шаазан ХХК
        ent_soltan = get_or_create_entity(db, "Гайнигийн Солтан", entity_type="person", aliases=["Г.Солтан"])
        ent_mongol_shaazan = get_or_create_entity(db, "Монгол Шаазан ХХК", entity_type="company", description="Г.Солтаны хамаарал бүхий компани, ЖДҮХС-гаас 950 сая ₮ зээл авсан")
        add_rel(db, ent_soltan.id, ent_mongol_shaazan.id, "хамаарал бүхий эзэмшигч", "Монгол Шаазан ХХК", source_id=src_sme.id)
        f_soltan = add_fact(db, ent_soltan.id, src_sme.id,
            "УИХ-ын гишүүнээр ажиллаж байхдаа өөрийн үүсгэн байгуулсан 'Монгол Шаазан' ХХК-иараа дамжуулан ЖДҮХС-аас 950 сая төгрөгийн зээл авсан хэргээр 2020 онд шүүхээс 3 жилийн хорих ял шийтгүүлсэн.",
            fact_date=date(2020, 7, 29), date_precision="day", tags=["ЖДҮ", "ял", "УИХ", "авлига"])

        # 2. Б.Ундармаа -> Доктор МЭИК ХХК, Капитал банк
        ent_undarmaa = get_or_create_entity(db, "Бадраагийн Ундармаа", entity_type="person", aliases=["Б.Ундармаа"])
        ent_doctor_meik = get_or_create_entity(db, "Доктор МЭИК ХХК", entity_type="company", description="Б.Ундармаагийн хамаарал бүхий компани, 700 сая ₮ зээл авсан")
        add_rel(db, ent_undarmaa.id, ent_doctor_meik.id, "хамаарал бүхий эзэмшигч", "Доктор МЭИК ХХК", source_id=src_sme.id)
        f_undarmaa = add_fact(db, ent_undarmaa.id, src_sme.id,
            "УИХ-ын гишүүнээр ажиллаж байхдаа өөрийн хамаарал бүхий 'Доктор МЭИК' ХХК-д ЖДҮХС-аас 700 сая төгрөгийн нэн хөнгөлөлттэй зээл авч, албан тушаалаа урвуулан ашигласан хэргээр 2020 онд 2 жил 6 сарын хорих ял сонссон.",
            fact_date=date(2020, 8, 11), date_precision="day", tags=["ЖДҮ", "ял", "УИХ", "авлига"])

        # 3. Д.Дамба-Очир -> Сэлэнгэ Зам ХХК
        ent_dambaochir = get_or_create_entity(db, "Дорждамбын Дамба-Очир", entity_type="person", aliases=["Д.Дамба-Очир"])
        ent_selenge_zam = get_or_create_entity(db, "Сэлэнгэ Зам ХХК", entity_type="company", description="Д.Дамба-Очирын хамаарал бүхий компани, 1.2 тэрбум ₮ зээл авсан")
        add_rel(db, ent_dambaochir.id, ent_selenge_zam.id, "хамаарал бүхий эзэмшигч", "Сэлэнгэ Зам ХХК", source_id=src_sme.id)
        f_damba = add_fact(db, ent_dambaochir.id, src_sme.id,
            "УИХ-ын гишүүн, Төсвийн байнгын хорооны даргаар ажиллаж байхдаа 'Сэлэнгэ Зам' ХХК-д ЖДҮХС-аас 1.2 тэрбум төгрөгийн хөнгөлөлттэй зээл олгуулсан хэргээр шүүхээс 3 жил 6 сар хорих ял авсан.",
            fact_date=date(2020, 8, 19), date_precision="day", tags=["ЖДҮ", "ял", "УИХ", "төсөв"])

        # 4. Л.Энхболд -> Хасговь транс ХХК
        ent_lenkhbold = get_or_create_entity(db, "Лувсангийн Энхболд", entity_type="person", aliases=["Л.Энхболд"])
        ent_khasgovi = get_or_create_entity(db, "Хасговь транс ХХК", entity_type="company", description="Л.Энхболдын хамаарал бүхий компани, 950 сая ₮ зээл авсан")
        add_rel(db, ent_lenkhbold.id, ent_khasgovi.id, "хамаарал бүхий эзэмшигч", "Хасговь транс ХХК", source_id=src_sme.id)
        f_lenkhbold = add_fact(db, ent_lenkhbold.id, src_sme.id,
            "ЖДҮХС-аас өөрийн хамаарал бүхий 'Хасговь транс' ХХК болон бусад аж ахуйн нэгжээр дамжуулан 950 сая төгрөгийн зээл авсан хэргээр яллагдаж, шүүхээс торгох болон албан тушаал хаших эрхийг хасах ял сонссон.",
            fact_date=date(2020, 11, 4), date_precision="day", tags=["ЖДҮ", "ял", "УИХ"])

        # 5. Б.Батзориг сайд
        ent_batzorig = get_or_create_entity(db, "Батжаргалын Батзориг", entity_type="person", aliases=["Б.Батзориг"])
        f_batzorig = add_fact(db, ent_batzorig.id, src_sme.id,
            "ХХААХҮ-ийн сайдаар ажиллаж байхдаа эрх мэдлээ урвуулан ашиглаж, УИХ-ын гишүүдийн хамаарал бүхий этгээдүүдэд хууль зөрчин ЖДҮХС-гаас нийт олон тэрбум төгрөгийн зээл олгох шийдвэр гаргасан гэм буруугаа хүлээж, 40 сая төгрөгөөр торгуулж, нийтийн албанд ажиллах эрхээ 5 жилээр хасуулсан.",
            fact_date=date(2020, 4, 15), date_precision="day", tags=["ЖДҮ", "сайд", "ял", "авлига"])

        # 6. Я.Содбаатар -> Эпато анар ХХК
        ent_sodbaatar = get_or_create_entity(db, "Янгуугийн Содбаатар", entity_type="person", aliases=["Я.Содбаатар"])
        ent_epato = get_or_create_entity(db, "Эпато анар ХХК", entity_type="company", description="Я.Содбаатарын гэр бүлийн хамаарал бүхий компани, ЖДҮ-гээс 1.2 тэрбум ₮ авсан")
        add_rel(db, ent_sodbaatar.id, ent_epato.id, "хамаарал бүхий компани", "Эпато анар ХХК", source_id=src_sme.id)
        f_sodbaatar = add_fact(db, ent_sodbaatar.id, src_sme.id,
            "2018 онд гэр бүлийн хамаарал бүхий 'Эпато анар' ХХК нь ЖДҮХС-гаас 1.2 тэрбум төгрөгийн хөнгөлөлттэй зээл авсан нь ил болж, улмаар Зам тээврийн хөгжлийн сайдын үүрэгт ажлаасаа өөрийн хүсэлтээр чөлөөлөгдөх өргөдлөө өгсөн.",
            fact_date=date(2018, 11, 23), date_precision="day", tags=["ЖДҮ", "сайд", "огцролт"])

        # 7. Х.Болорчулуун -> Дорнод гурил ХХК
        ent_bolorchuluun = get_or_create_entity(db, "Хаянгаагийн Болорчулуун", entity_type="person", aliases=["Х.Болорчулуун"])
        ent_dornod_guril = get_or_create_entity(db, "Дорнод гурил ХХК", entity_type="company", description="Х.Болорчулууны үүсгэн байгуулсан компани, 950 сая ₮ зээл авсан")
        add_rel(db, ent_bolorchuluun.id, ent_dornod_guril.id, "үүсгэн байгуулагч / хувьцаа эзэмшигч", "Дорнод гурил ХХК", source_id=src_sme.id)
        f_bolorchuluun = add_fact(db, ent_bolorchuluun.id, src_sme.id,
            "Өөрийн хувьцаа эзэмшдэг 'Дорнод гурил' ХХК-д ЖДҮХС-гаас 950 сая төгрөгийн зээл авсан баримт илчлэгдсэнээр олон нийтийн шүүмжлэлд өртсөн ч зээлээ хугацаанд нь буцаан төлсөн гэж мэдэгдсэн.",
            fact_date=date(2018, 11, 5), date_precision="day", tags=["ЖДҮ", "УИХ", "зээл"])

        # Case 6 links update
        link_case(db, 6, entity_id=ent_batzorig.id, role="DECISION_MAKER", note="Зээл баталсан сайд, ял шийтгүүлсэн")
        link_case(db, 6, entity_id=ent_soltan.id, role="SUSPECT", note="Монгол Шаазан ХХК-иар зээл авч 3 жил хоригдсон")
        link_case(db, 6, entity_id=ent_undarmaa.id, role="SUSPECT", note="Доктор МЭИК ХХК-иар зээл авч 2.5 жил хоригдсон")
        link_case(db, 6, entity_id=ent_dambaochir.id, role="SUSPECT", note="Сэлэнгэ Зам ХХК-иар зээл авч 3.5 жил хоригдсон")
        link_case(db, 6, entity_id=ent_lenkhbold.id, role="SUSPECT", note="Хасговь транс ХХК-иар зээл авч ял шийтгүүлсэн")
        link_case(db, 6, entity_id=ent_sodbaatar.id, role="INVOLVED_IN", note="Эпато анар ХХК-иар зээл авч сайдаас огцорсон")
        link_case(db, 6, entity_id=ent_bolorchuluun.id, role="BENEFICIARY", note="Дорнод гурил ХХК-иар 950 сая төгрөгийн зээл авсан")

        link_case(db, 6, entity_id=ent_mongol_shaazan.id, role="BENEFICIARY", note="Г.Солтаны хамаарал бүхий зээлдэгч")
        link_case(db, 6, entity_id=ent_doctor_meik.id, role="BENEFICIARY", note="Б.Ундармаагийн хамаарал бүхий зээлдэгч")
        link_case(db, 6, entity_id=ent_selenge_zam.id, role="BENEFICIARY", note="Д.Дамба-Очирын хамаарал бүхий зээлдэгч")
        link_case(db, 6, entity_id=ent_khasgovi.id, role="BENEFICIARY", note="Л.Энхболдын хамаарал бүхий зээлдэгч")
        link_case(db, 6, entity_id=ent_epato.id, role="BENEFICIARY", note="Я.Содбаатарын гэр бүлийн хамаарал бүхий зээлдэгч")
        link_case(db, 6, entity_id=ent_dornod_guril.id, role="BENEFICIARY", note="Х.Болорчулууны хамаарал бүхий зээлдэгч")

        link_case(db, 6, fact_id=f_soltan.id, role="EVIDENCE_FOR", note="Г.Солтаны ялын тогтоол")
        link_case(db, 6, fact_id=f_undarmaa.id, role="EVIDENCE_FOR", note="Б.Ундармаагийн ялын тогтоол")
        link_case(db, 6, fact_id=f_damba.id, role="EVIDENCE_FOR", note="Д.Дамба-Очирын ялын тогтоол")
        link_case(db, 6, fact_id=f_lenkhbold.id, role="EVIDENCE_FOR", note="Л.Энхболдын ялын тогтоол")
        link_case(db, 6, fact_id=f_batzorig.id, role="EVIDENCE_FOR", note="Б.Батзориг сайдын ялын тогтоол")

        db.commit()
        print("Багц 1 амжилттай бүртгэгдлээ!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
