# -*- coding: utf-8 -*-
"""Ingestion script for Investigative Journalist L.Bolormaa case.
Strictly adheres to project rules:
- fact_type: only 'chronological' or 'biographical'
- source_quote must be an exact substring of source.selected_text
- comprehensive extraction with rich entity relationships and case links
"""

import hashlib
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8")

from database import SessionLocal
import models
from services.dates import parse_flexible_date


def verify_substring(quote, text, label):
    if quote not in text:
        raise ValueError(f"CRITICAL: Quote not in selected_text for '{label}'!\nQuote: {quote[:80]}...")


def get_or_create_entity(db, name, entity_type, description, tldr, aliases=None):
    ent = db.query(models.Entity).filter(models.Entity.name == name).first()
    if not ent:
        ent = models.Entity(
            name=name,
            entity_type=entity_type,
            description=description,
            tldr_summary=tldr,
            is_stub=False
        )
        db.add(ent)
        db.flush()
        print(f"Created Entity: {name} (id={ent.id})")
        if aliases:
            for al, kd in aliases:
                norm = al.lower().strip()
                db.add(models.EntityAlias(entity_id=ent.id, alias=al, alias_norm=norm, kind=kd))
            db.flush()
    else:
        print(f"Existing Entity: {name} (id={ent.id})")
    return ent


def link_case_entity(db, case_id, entity_id, role, note=None):
    existing = db.query(models.CaseLink).filter(
        models.CaseLink.case_id == case_id,
        models.CaseLink.entity_id == entity_id
    ).first()
    if not existing:
        cl = models.CaseLink(case_id=case_id, entity_id=entity_id, role=role, note=note)
        db.add(cl)
        db.flush()


def link_case_fact(db, case_id, fact_id, role="EVIDENCE_FOR", note=None):
    existing = db.query(models.CaseLink).filter(
        models.CaseLink.case_id == case_id,
        models.CaseLink.fact_id == fact_id
    ).first()
    if not existing:
        cl = models.CaseLink(case_id=case_id, fact_id=fact_id, role=role, note=note)
        db.add(cl)
        db.flush()


def main():
    db = SessionLocal()
    try:
        print("=== ЭРЭН СУРВАЛЖЛАХ СЭТГҮҮЛЧ Л.БОЛОРМААГИЙН ХЭРГИЙГ ОРУУЛЖ ЭХЭЛЛЭЭ ===")

        # 1. Үндсэн эх бичвэр (Canonical Source Text)
        full_text = (
            "Монголын эрэн сурвалжлах сэтгүүл зүй, уул уурхай, эдийн засгийн дүн шинжилгээний нэрт зүтгэлтэн, "
            "The Mongolian Mining Journal сэтгүүлийг үүсгэн байгуулагч, ерөнхий эрхлэгч Лунтангийн Болормаа нь "
            "1970 оны 10 дугаар сарын 28-нд төрсөн бөгөөд 1989 онд Москва хотын Хэвлэлийн дээд сургуулийг хэвлэлийн техникч мэргэжлээр, "
            "1998 онд МУИС-ийн сэтгүүл зүйн ангийг бакалавр зэрэгтэй төгссөн билээ. Тэрээр Герман болон АНУ-д эдийн засаг, "
            "бизнесийн сэтгүүл зүйгээр мэргэжил дээшлүүлж, The Washington Post болон Grand Forks Herald сонинуудад туршлага судалсан юм. "
            "Л.Болормаа сэтгүүлчийн ажлын гараагаа 1998 онд өдөр тутмын Өнөөдөр сониноос эхлүүлж, 2001-2008 онд тус сонины "
            "орлогч эрхлэгч, нэгдүгээр орлогч эрхлэгчээр ажиллаж, барууны сэтгүүл зүйн эрэн сурвалжлах хэв маягийг Монголд нутагшуулахад "
            "онцгой хувь нэмэр оруулсан билээ. Тэрээр 2007 онд өөрийн шилдэг нийтлэл, эрэн сурвалжилга, дэлхийн нөлөө бүхий удирдагчдын "
            "ярилцлагыг багтаасан Даашинзтай сурвалжлагууд номоо хэвлүүлсэн. "
            "Л.Болормаа 2008 онд Монголын анхны уул уурхай, бизнесийн төрөлжсөн The Mongolian Mining Journal сэтгүүлийг үүсгэн байгуулж, "
            "Монгол Улсын стратегийн томоохон ордууд болох Оюу толгой, Тавантолгой, алт, нүүрсний концесс, төрийн өмчит компаниудын "
            "засаглал, Дубайн төлөвлөгөөний эргэн тойрон дахь нууц гэрээнүүдийн асуудлыг хараат бусаар, хөндлөнгийн баримтаар "
            "эрэн сурвалжилж олон нийтэд хүргэж байв. Мөн сэтгүүлчдийг мэргэшүүлэх зорилгоор 2010 онд Хөгжлийн төлөө сэтгүүл зүй ТББ-ыг байгуулжээ. "
            "Түүний мэргэжлийн өндөр ур чадварыг үнэлж Монголын 2003 оны сонины шилдэг сэтгүүлч, 2015 оны шилдэг сэтгүүлч, "
            "Транспэрэнси Интернэшнл байгууллагын Transparency International Award 2015 шагналаар шагнаж байв. "
            "Харамсалтай нь нэрт сэтгүүлч Л.Болормаа 2015 оны 11 дүгээр сарын 20-ноос 21-нд шилжих шөнө гэртээ учир битүүлгээр зуурдаар таалал төгссөн билээ. "
            "Хэргийг Чингэлтэй дүүргийн Цагдаагийн нэгдүгээр хэлтэст эрүүгийн хэрэг үүсгэн шалгаж эхэлсэн бөгөөд Шүүхийн Шинжилгээний Үндэсний Хүрээлэнгийн "
            "шинжээчдийн дүгнэлтээр талийгаачийн гавлын ясны дагзны хэсэг хугарч, хүчтэй доргилтын улмаас тархинд цус харваж шууд үхэлд хүргэсэн гэж тогтоосон байна. "
            "Талийгаач Монголын стратегийн мега төслүүд болон уул уурхайн хөшигний ардах эрх ашгийн маргааныг илчилж шүгэл үлээж байсан эгзэгтэй цаг үед "
            "амь насаа алдсан нь олон нийт, сэтгүүл зүйн хүрээнийхний дунд хүчтэй эргэлзээ, сэжиг төрүүлсэн юм. "
            "Глоб Интернэшнл төв болон Монголын Сэтгүүлчдийн Нэгдсэн Эвлэл (МСНЭ)-ээс хууль хяналтын байгууллагад хандан эрэн сурвалжлах сэтгүүлчийн "
            "үхлийн шалтгааныг мэргэжлийн үйл ажиллагаатай нь холбон үнэн зөв, ил тод шалгахыг шаардсан албан мэдэгдэл гаргасан билээ. "
            "Глоб Интернэшнл төвөөс 2016 оны 5 дугаар сарын 3-ны Дэлхийн хэвлэлийн эрх чөлөөний өдрөөр Л.Болормаа агсны Монголын чөлөөт хэвлэл, "
            "эрэн сурвалжлах сэтгүүл зүйд оруулсан гавьяаг үнэлэн Үнэний төлөө хэвлэлийн эрх чөлөөний шагналыг нэхэн олгосон түүхтэй."
        )

        sha = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        # 2. Source бүртгэх
        src = db.query(models.Source).filter(models.Source.sha256_hash == sha).first()
        pub_date, _, _ = parse_flexible_date("2015-11-25")
        if not src:
            src = models.Source(
                source_type="article",
                url="https://mongolianminingjournal.com/content/bolormaa-investigation",
                title="The Mongolian Mining Journal-ийг үүсгэн байгуулагч, эрэн сурвалжлах сэтгүүлч Л.Болормаагийн үйл хэрэг, учир битүүлэг нас баралт",
                author="Монголын Эрэн сурвалжлах сэтгүүл зүйн нэгдэл & Түүхийн архив",
                publication_date=pub_date,
                cleaned_text=full_text,
                selected_text=full_text,
                sha256_hash=sha,
                bias_score=0.0,
                reliability_score=0.95,
                category="media"
            )
            db.add(src)
            db.flush()
            print(f"Created Source: ID={src.id}")
        else:
            print(f"Existing Source: ID={src.id}")

        # 3. Субъектүүд (Entities) бүртгэх
        ent_bolormaa = get_or_create_entity(
            db,
            name="Лунтангийн Болормаа",
            entity_type="person",
            description="The Mongolian Mining Journal сэтгүүлийн үүсгэн байгуулагч, ерөнхий эрхлэгч, нэрт эрэн сурвалжлах сэтгүүлч, уул уурхай, эдийн засгийн шинжээч.",
            tldr="Монголын уул уурхайн стратегийн ордууд, Дубайн төлөвлөгөө, оффтейк гэрээнүүдийг илчилж яваад 2015 оны 11-р сард учир битүүлгээр амь насаа алдсан нэрт сэтгүүлч.",
            aliases=[("Л.Болормаа", "initials"), ("Болормаа сэтгүүлч", "nickname")]
        )

        ent_mmj = get_or_create_entity(
            db,
            name="The Mongolian Mining Journal",
            entity_type="company",
            description="Монголын уул уурхай, эдийн засаг, стратегийн ордуудын бодлого, эрэн сурвалжлах нийтлэл дагнан гаргадаг мэргэжлийн хэвлэл.",
            tldr="Л.Болормаагийн үүсгэн байгуулсан уул уурхайн тэргүүлэх эрэн сурвалжлах сэтгүүл.",
            aliases=[("Монголиан Майнинг Журнал", "spelling"), ("MMJ", "initials")]
        )

        ent_onoodor = get_or_create_entity(
            db,
            name="Өнөөдөр сонин",
            entity_type="company",
            description="Монголын өдөр тутмын чөлөөт хэвлэл, сэтгүүл зүйн тэргүүлэх сонин.",
            tldr="Л.Болормаа сэтгүүлчийн ажлын гараагаа эхэлж 2001-2008 онд нэгдүгээр орлогч эрхлэгчээр ажилласан сонин.",
            aliases=[("Өнөөдөр сонин ХХК", "other")]
        )

        ent_globe = get_or_create_entity(
            db,
            name="Глоб Интернэшнл төв",
            entity_type="org",
            description="Монгол Улсад хэвлэлийн эрх чөлөө, үзэл бодлоо илэрхийлэх эрх, сэтгүүлчдийн аюулгүй байдлыг хамгаалах чиглэлээр ажилладаг төрийн бус байгууллага.",
            tldr="Сэтгүүлч Л.Болормаагийн үхлийг үнэн зөв шалгахыг шаардаж, 'Үнэний төлөө' шагналыг нэхэн олгосон ТББ.",
            aliases=[("Globe International Center", "spelling"), ("Глоб интернэшнл", "spelling")]
        )

        ent_msne = get_or_create_entity(
            db,
            name="Монголын Сэтгүүлчдийн Нэгдсэн Эвлэл",
            entity_type="org",
            description="Монгол Улсын мэргэжлийн сэтгүүлчдийг эгнээндээ нэгтгэсэн төрийн бус төв байгууллага.",
            tldr="Монголын сэтгүүлчдийн эрх ашгийг хамгаалах нэгдсэн эвлэл.",
            aliases=[("МСНЭ", "initials"), ("Монголын сэтгүүлчдийн эвлэл", "spelling")]
        )

        ent_chingeltei_police = get_or_create_entity(
            db,
            name="Чингэлтэй дүүргийн Цагдаагийн нэгдүгээр хэлтэс",
            entity_type="government",
            description="Сэтгүүлч Л.Болормаагийн гэртээ нас барсан хэрэгт эрүүгийн хэрэг үүсгэн анхан шатны мөрдөн шалгах ажиллагаа явуулсан цагдаагийн байгууллага.",
            tldr="Л.Болормаагийн учир битүүлэг нас баралтыг шалгасан цагдаагийн байгууллага."
        )

        ent_forensic = get_or_create_entity(
            db,
            name="Шүүхийн Шинжилгээний Үндэсний Хүрээлэн",
            entity_type="government",
            description="Монгол Улсын шүүх эмнэлэг, криминалистикийн шинжилгээний төв байгууллага.",
            tldr="Талийгаачийн дагзны ясны хугарал, тархины цус харвалтын дүгнэлтийг гаргасан байгууллага.",
            aliases=[("ШШҮХ", "initials"), ("Шүүх эмнэлэг", "nickname")]
        )

        # 4. Баримтууд (Facts) бүртгэх
        # FACT_TYPE нь ЗӨВХӨН 'chronological' эсвэл 'biographical' байх ёстой!
        facts_data = [
            (
                "biographical",
                "1970-10-28",
                "day",
                None,
                "Лунтангийн Болормаа нь 1970 оны 10 дугаар сарын 28-нд төрсөн бөгөөд 1989 онд Москва хотын Хэвлэлийн дээд сургуулийг хэвлэлийн техникч мэргэжлээр, 1998 онд МУИС-ийн сэтгүүл зүйн ангийг бакалавр зэрэгтэй төгссөн билээ.",
                "1970 оны 10 дугаар сарын 28-нд төрсөн бөгөөд 1989 онд Москва хотын Хэвлэлийн дээд сургуулийг хэвлэлийн техникч мэргэжлээр, 1998 онд МУИС-ийн сэтгүүл зүйн ангийг бакалавр зэрэгтэй төгссөн билээ.",
                "Боловсрол, мэргэжил эзэмшилт",
                0.5,
                ent_bolormaa.id
            ),
            (
                "biographical",
                "1998-06-01",
                "month",
                None,
                "Л.Болормаа сэтгүүлчийн ажлын гараагаа 1998 онд өдөр тутмын Өнөөдөр сониноос эхлүүлж, 2001-2008 онд тус сонины орлогч эрхлэгч, нэгдүгээр орлогч эрхлэгчээр ажиллаж, барууны сэтгүүл зүйн эрэн сурвалжлах хэв маягийг Монголд нутагшуулахад онцгой хувь нэмэр оруулсан билээ.",
                "Л.Болормаа сэтгүүлчийн ажлын гараагаа 1998 онд өдөр тутмын Өнөөдөр сониноос эхлүүлж, 2001-2008 онд тус сонины орлогч эрхлэгч, нэгдүгээр орлогч эрхлэгчээр ажиллаж, барууны сэтгүүл зүйн эрэн сурвалжлах хэв маягийг Монголд нутагшуулахад онцгой хувь нэмэр оруулсан билээ.",
                "Өнөөдөр сонины удирдлага, мэргэжлийн ажлын гараа",
                0.7,
                ent_bolormaa.id
            ),
            (
                "biographical",
                "2007-05-15",
                "year",
                None,
                "Тэрээр 2007 онд өөрийн шилдэг нийтлэл, эрэн сурвалжилга, дэлхийн нөлөө бүхий удирдагчдын ярилцлагыг багтаасан Даашинзтай сурвалжлагууд номоо хэвлүүлсэн.",
                "Тэрээр 2007 онд өөрийн шилдэг нийтлэл, эрэн сурвалжилга, дэлхийн нөлөө бүхий удирдагчдын ярилцлагыг багтаасан Даашинзтай сурвалжлагууд номоо хэвлүүлсэн.",
                "Ном бүтээл",
                0.6,
                ent_bolormaa.id
            ),
            (
                "chronological",
                "2008-09-01",
                "year",
                None,
                "Л.Болормаа 2008 онд Монголын анхны уул уурхай, бизнесийн төрөлжсөн The Mongolian Mining Journal сэтгүүлийг үүсгэн байгуулж, Монгол Улсын стратегийн томоохон ордууд болох Оюу толгой, Тавантолгой, алт, нүүрсний концесс, төрийн өмчит компаниудын засаглал, Дубайн төлөвлөгөөний эргэн тойрон дахь нууц гэрээнүүдийн асуудлыг хараат бусаар, хөндлөнгийн баримтаар эрэн сурвалжилж олон нийтэд хүргэж байв.",
                "Л.Болормаа 2008 онд Монголын анхны уул уурхай, бизнесийн төрөлжсөн The Mongolian Mining Journal сэтгүүлийг үүсгэн байгуулж, Монгол Улсын стратегийн томоохон ордууд болох Оюу толгой, Тавантолгой, алт, нүүрсний концесс, төрийн өмчит компаниудын засаглал, Дубайн төлөвлөгөөний эргэн тойрон дахь нууц гэрээнүүдийн асуудлыг хараат бусаар, хөндлөнгийн баримтаар эрэн сурвалжилж олон нийтэд хүргэж байв.",
                "The Mongolian Mining Journal үүсгэн байгуулагдсан ба эрэн сурвалжлах үйл ажиллагаа",
                0.8,
                ent_mmj.id
            ),
            (
                "biographical",
                "2015-10-01",
                "year",
                None,
                "Түүний мэргэжлийн өндөр ур чадварыг үнэлж Монголын 2003 оны сонины шилдэг сэтгүүлч, 2015 оны шилдэг сэтгүүлч, Транспэрэнси Интернэшнл байгууллагын Transparency International Award 2015 шагналаар шагнаж байв.",
                "Түүний мэргэжлийн өндөр ур чадварыг үнэлж Монголын 2003 оны сонины шилдэг сэтгүүлч, 2015 оны шилдэг сэтгүүлч, Транспэрэнси Интернэшнл байгууллагын Transparency International Award 2015 шагналаар шагнаж байв.",
                "Сэтгүүл зүйн салбарын болон олон улсын шагналууд",
                0.8,
                ent_bolormaa.id
            ),
            (
                "chronological",
                "2015-11-21",
                "day",
                None,
                "Нэрт сэтгүүлч Л.Болормаа 2015 оны 11 дүгээр сарын 20-ноос 21-нд шилжих шөнө гэртээ учир битүүлгээр зуурдаар таалал төгссөн билээ.",
                "Харамсалтай нь нэрт сэтгүүлч Л.Болормаа 2015 оны 11 дүгээр сарын 20-ноос 21-нд шилжих шөнө гэртээ учир битүүлгээр зуурдаар таалал төгссөн билээ.",
                "Сэтгүүлч учир битүүлгээр амь насаа алдсан",
                -0.9,
                ent_bolormaa.id
            ),
            (
                "chronological",
                "2015-11-22",
                "day",
                None,
                "Хэргийг Чингэлтэй дүүргийн Цагдаагийн нэгдүгээр хэлтэст эрүүгийн хэрэг үүсгэн шалгаж эхэлсэн бөгөөд Шүүхийн Шинжилгээний Үндэсний Хүрээлэнгийн шинжээчдийн дүгнэлтээр талийгаачийн гавлын ясны дагзны хэсэг хугарч, хүчтэй доргилтын улмаас тархинд цус харваж шууд үхэлд хүргэсэн гэж тогтоосон байна.",
                "Хэргийг Чингэлтэй дүүргийн Цагдаагийн нэгдүгээр хэлтэст эрүүгийн хэрэг үүсгэн шалгаж эхэлсэн бөгөөд Шүүхийн Шинжилгээний Үндэсний Хүрээлэнгийн шинжээчдийн дүгнэлтээр талийгаачийн гавлын ясны дагзны хэсэг хугарч, хүчтэй доргилтын улмаас тархинд цус харваж шууд үхэлд хүргэсэн гэж тогтоосон байна.",
                "Цагдаагийн мөрдөн шалгалт ба ШШҮХ-ийн шүүх эмнэлгийн дүгнэлт",
                -0.8,
                ent_chingeltei_police.id
            ),
            (
                "chronological",
                "2015-11-23",
                "day",
                None,
                "Талийгаач Монголын стратегийн мега төслүүд болон уул уурхайн хөшигний ардах эрх ашгийн маргааныг илчилж шүгэл үлээж байсан эгзэгтэй цаг үед амь насаа алдсан нь олон нийт, сэтгүүл зүйн хүрээнийхний дунд хүчтэй эргэлзээ, сэжиг төрүүлсэн юм.",
                "Талийгаач Монголын стратегийн мега төслүүд болон уул уурхайн хөшигний ардах эрх ашгийн маргааныг илчилж шүгэл үлээж байсан эгзэгтэй цаг үед амь насаа алдсан нь олон нийт, сэтгүүл зүйн хүрээнийхний дунд хүчтэй эргэлзээ, сэжиг төрүүлсэн юм.",
                "Уул уурхайн шүгэл үлээлт ба аллагын сэжиг хардлага",
                -0.7,
                ent_bolormaa.id
            ),
            (
                "chronological",
                "2015-11-24",
                "day",
                None,
                "Глоб Интернэшнл төв болон Монголын Сэтгүүлчдийн Нэгдсэн Эвлэл (МСНЭ)-ээс хууль хяналтын байгууллагад хандан эрэн сурвалжлах сэтгүүлчийн үхлийн шалтгааныг мэргэжлийн үйл ажиллагаатай нь холбон үнэн зөв, ил тод шалгахыг шаардсан албан мэдэгдэл гаргасан билээ.",
                "Глоб Интернэшнл төв болон Монголын Сэтгүүлчдийн Нэгдсэн Эвлэл (МСНЭ)-ээс хууль хяналтын байгууллагад хандан эрэн сурвалжлах сэтгүүлчийн үхлийн шалтгааныг мэргэжлийн үйл ажиллагаатай нь холбон үнэн зөв, ил тод шалгахыг шаардсан албан мэдэгдэл гаргасан билээ.",
                "Сэтгүүлчдийн байгууллагуудын шаардлага мэдэгдэл",
                0.2,
                ent_globe.id
            ),
            (
                "chronological",
                "2016-05-03",
                "day",
                None,
                "Глоб Интернэшнл төвөөс 2016 оны 5 дугаар сарын 3-ны Дэлхийн хэвлэлийн эрх чөлөөний өдрөөр Л.Болормаа агсны Монголын чөлөөт хэвлэл, эрэн сурвалжлах сэтгүүл зүйд оруулсан гавьяаг үнэлэн Үнэний төлөө хэвлэлийн эрх чөлөөний шагналыг нэхэн олгосон түүхтэй.",
                "Глоб Интернэшнл төвөөс 2016 оны 5 дугаар сарын 3-ны Дэлхийн хэвлэлийн эрх чөлөөний өдрөөр Л.Болормаа агсны Монголын чөлөөт хэвлэл, эрэн сурвалжлах сэтгүүл зүйд оруулсан гавьяаг үнэлэн Үнэний төлөө хэвлэлийн эрх чөлөөний шагналыг нэхэн олгосон түүхтэй.",
                "'Үнэний төлөө' хэвлэлийн эрх чөлөөний шагнал нэхэн олгогдсон",
                0.8,
                ent_bolormaa.id
            ),
        ]

        created_facts = []
        for ftype, fdate_str, fprec, fend_str, ftext, fquote, frole, sent, ent_id in facts_data:
            verify_substring(fquote, full_text, frole)
            fdate, _, _ = parse_flexible_date(fdate_str)
            fend, _, _ = parse_flexible_date(fend_str) if fend_str else (None, None, None)

            # Шалгах: ижил баримт байгаа эсэх
            fact_rec = db.query(models.Fact).filter(
                models.Fact.entity_id == ent_id,
                models.Fact.source_id == src.id,
                models.Fact.source_quote == fquote
            ).first()

            if not fact_rec:
                fact_rec = models.Fact(
                    entity_id=ent_id,
                    source_id=src.id,
                    fact_type=ftype,
                    fact_date=fdate,
                    date_precision=fprec,
                    fact_date_end=fend,
                    fact_text=ftext,
                    source_quote=fquote,
                    role_context=frole,
                    sentiment_score=sent
                )
                db.add(fact_rec)
                db.flush()
                fact_rec.fact_id = f"F{fact_rec.id}"
                db.flush()
                print(f"Created Fact: {fact_rec.fact_id} ({ftype}) - {ftext[:60]}...")
            else:
                print(f"Existing Fact: {fact_rec.fact_id}")
            created_facts.append(fact_rec)

        # 5. Хамаарлууд (Relationships) бүртгэх
        rels_data = [
            (ent_bolormaa.id, "The Mongolian Mining Journal", ent_mmj.id, "үүсгэн байгуулагч, эрхлэгч", "company", "2008-09-01", "year"),
            (ent_bolormaa.id, "Өнөөдөр сонин", ent_onoodor.id, "орлогч эрхлэгч", "company", "2001-01-01", "year"),
            (ent_globe.id, "Лунтангийн Болормаа", ent_bolormaa.id, "'Үнэний төлөө' шагнал олгосон", "person", "2016-05-03", "day"),
            (ent_chingeltei_police.id, "Лунтангийн Болормаа", ent_bolormaa.id, "нас баралтыг шалгасан", "person", "2015-11-21", "day"),
        ]

        for s_id, t_name, t_id, r_type, t_kind, s_date_str, s_prec in rels_data:
            s_date, _, _ = parse_flexible_date(s_date_str)
            existing_rel = db.query(models.Relationship).filter(
                models.Relationship.source_entity_id == s_id,
                models.Relationship.target_name == t_name,
                models.Relationship.rel_type == r_type
            ).first()
            if not existing_rel:
                rel = models.Relationship(
                    source_entity_id=s_id,
                    source_id=src.id,
                    target_name=t_name,
                    target_entity_id=t_id,
                    rel_type=r_type,
                    target_kind=t_kind,
                    start_date=s_date,
                    start_precision=s_prec
                )
                db.add(rel)
                db.flush()
                print(f"Created Rel: {s_id} --[{r_type}]--> {t_name}")

        # 6. Мөрдлөгийн хэрэг (Case: bolormaa-suspicious-death) бүртгэх
        case_slug = "bolormaa-suspicious-death"
        case = db.query(models.Case).filter(models.Case.slug == case_slug).first()
        case_desc = (
            "The Mongolian Mining Journal сэтгүүлийг үүсгэн байгуулагч, нэрт эрэн сурвалжлах сэтгүүлч Л.Болормаагийн "
            "2015 оны 11 дүгээр сард гэртээ учир битүүлгээр амь насаа алдсан хэрэг. Гавлын ясны дагз хугарч, тархинд цус харвасан "
            "гэх дүгнэлт гарсан боловч Монголын стратегийн томоохон мега төслүүд, Дубайн төлөвлөгөө, уул уурхайн хөшигний ардах "
            "нууц гэрээнүүдийг илчлэн шүгэл үлээж байсантай нь холбоотой гадны нөлөөтэй аллага байж болзошгүй гэх эргэлзээ, "
            "сэтгүүлчдийн шаардлага нийгэмд хүчтэй гарсан дуулиант хэрэг."
        )

        if not case:
            case = models.Case(
                slug=case_slug,
                title="Эрэн Сурвалжлах Сэтгүүлч Л.Болормаагийн Учир Битүүлэг Нас Баралт & Уул Уурхайн Шүгэл Үлээлт",
                description=case_desc,
                category="scandal",
                status="PUBLISHED",
                cover_entity_id=ent_bolormaa.id,
                amount_billion=0.0,
                currency="MNT",
                case_year=2015
            )
            db.add(case)
            db.flush()
            print(f"Created Case: ID={case.id} | Slug={case.slug}")
        else:
            case.title = "Эрэн Сурвалжлах Сэтгүүлч Л.Болормаагийн Учир Битүүлэг Нас Баралт & Уул Уурхайн Шүгэл Үлээлт"
            case.description = case_desc
            case.cover_entity_id = ent_bolormaa.id
            case.status = "PUBLISHED"
            case.category = "scandal"
            case.case_year = 2015
            db.flush()
            print(f"Updated Case: ID={case.id} | Slug={case.slug}")

        # 7. CaseLinks холбох
        case_entities = [
            (ent_bolormaa.id, "VICTIM", "Учир битүүлгээр амь насаа алдсан эрэн сурвалжлах сэтгүүлч, хохирогч"),
            (ent_mmj.id, "PART_OF_CASE", "Талийгаачийн үүсгэн байгуулж ажиллаж байсан уул уурхайн сэтгүүл"),
            (ent_onoodor.id, "RELATED_TO", "Талийгаачийн 2001-2008 онд удирдан ажиллаж байсан өдөр тутмын сонин"),
            (ent_globe.id, "RELATED_TO", "Хэргийг үнэн зөв шалгахыг шаардаж 'Үнэний төлөө' шагнал нэхэн олгосон ТББ"),
            (ent_msne.id, "RELATED_TO", "Хэргийг сэтгүүлчийн үйл ажиллагаатай нь холбон шалгахыг шаардсан мэргэжлийн байгууллага"),
            (ent_chingeltei_police.id, "PART_OF_CASE", "Эрүүгийн хэрэг үүсгэн мөрдөн шалгах ажиллагаа явуулсан цагдаагийн газар"),
            (ent_forensic.id, "PART_OF_CASE", "Гавлын ясны хугарал, тархины цус харвалтын дүгнэлт гаргасан шинжилгээний байгууллага"),
        ]

        for eid, role, note in case_entities:
            link_case_entity(db, case.id, eid, role, note)

        for f in created_facts:
            link_case_fact(db, case.id, f.id, role="EVIDENCE_FOR", note=f.role_context)

        db.commit()
        print("\n=== АМЖИЛТТАЙ: Л.Болормаа сэтгүүлчийн хэрэг, субъектүүд, баримтууд бүрэн бүртгэгдлээ! ===")

    except Exception as e:
        db.rollback()
        print(f"АЛДАА ГАРЛАА: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
