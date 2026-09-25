# -*- coding: utf-8 -*-
"""Ingest additional coal articles: ikon_2qfn and news_2694237."""

import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
sys.stdout.reconfigure(encoding="utf-8")

from database import SessionLocal
import models
from services.dates import parse_flexible_date
from services import importing
from hasher import stable_hash
import scraper


def verify_substring(quote, text, label):
    if quote not in text:
        raise ValueError(f"CRITICAL: Quote not in selected_text for '{label}'!\nQuote: {quote[:80]}...")


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
        case = db.query(models.Case).filter(models.Case.slug == "coal-theft").first()
        case_id = case.id

        # -------------------------------------------------------------
        # Source 11: ikon_2qfn (Д.Амарбаясгалангийн мэдээлэл)
        # -------------------------------------------------------------
        url_2qfn = "https://ikon.mn/n/2qfn"
        src_2qfn = db.query(models.Source).filter(models.Source.url == url_2qfn).first()
        scraped_2qfn = scraper.scrape(url_2qfn)
        blocks_2qfn = [
            b["text"].strip() for b in scraped_2qfn.get("blocks", [])
            if len(b["text"].strip()) > 10
            and not b["text"].startswith("© 2017 -")
            and not b["text"].startswith("[email")
            and not b["text"].startswith("Хэвлэл мэдээллийн байгууллагууд")
            and not b["text"].startswith("9 сарын 23, Лхагва")
            and not b["text"].startswith("7°C Улаанбаатар")
            and not b["text"].startswith("Уншиж байна ...")
        ]
        text_2qfn = "\n\n".join(blocks_2qfn)
        if not src_2qfn:
            src_2qfn = models.Source(
                source_type="article",
                category="media",
                url=url_2qfn,
                title="“Нүүрсний хулгайн асуудал эцэслэгдэн шийдвэрлэгдээгүй байна. Богино хугацаанд ил тод болгож, олон нийтэд мэдээлнэ“",
                author="Б.Даваабазар, iKon.mn",
                publication_date=parse_flexible_date("2022-11-30")[0],
                cleaned_text=text_2qfn,
                selected_text=text_2qfn,
                raw_hash=stable_hash(text_2qfn),
                sha256_hash=stable_hash(text_2qfn),
                bias_score=0.9,
                reliability_score=0.9,
            )
            db.add(src_2qfn)
            db.flush()
            print(f"Created Source: {src_2qfn.title} (id={src_2qfn.id})")
        else:
            print(f"Existing Source: {src_2qfn.title} (id={src_2qfn.id})")

        amarbayasgalan = db.query(models.Entity).filter(models.Entity.name == "Дашзэгвийн Амарбаясгалан").first()
        ett = db.query(models.Entity).filter(models.Entity.name == "Эрдэнэс Тавантолгой ХК").first()

        facts_2qfn = [
            {
                "entity_id": amarbayasgalan.id,
                "fact_type": "chronological",
                "fact": "Монгол Улс, БНХАУ-ын прокурорын байгууллагууд Монголоос гарсан болон БНХАУ руу орсон нүүрсний гаалийн мэдүүлгийг тулган нягтлах хамтарсан үйл ажиллагааг хэрэгжүүлэх хүсэлтийг Засгийн газарт хүргүүлж, 6 сайдад дэмжин ажиллах үүрэг өгсөн.",
                "source_quote": "Тодруулбал, хоёр улсын прокурорын байгууллагууд Монгол Улсаас гарч байгаа нүүрсний гаалийн мэдүүлэг, БНХАУ руу орсон нүүрсний гаалийн мэдүүлэг хоёрыг тулган нягтлах үйл ажиллагааг хамтарч хэрэгжүүлэх саналтай байна. Үүнийг Засгийн газрын зүгээс дэмжиж ажиллаач гэх албан хүсэлт ирсэн.",
                "role_context": "Хил дамнасан гаалийн мэдүүлэг тулгалт",
                "start_date": "2022-11-30",
                "tags": ["гаалийн_мэдүүлэг", "бнхау", "прокурор", "тулгалт"],
            },
            {
                "entity_id": ett.id,
                "fact_type": "chronological",
                "fact": "2017 оноос хойш 'Эрдэнэс Тавантолгой' болон орон нутгийн 'Тавантолгой' компанийн хооронд үүссэн нүүрсний зөрүү, алдагдлын ул мөрийг ЦЕГ-ын Эдийн засгийн гэмт хэрэгтэй тэмцэх нэгж дээр шалгаж буйг Засгийн газар мэдэгдсэн.",
                "source_quote": "Үүний ул мөрөөр ЦЕГ-ын эдийн засгийн гэмт хэрэгтэй тэмцэх нэгж дээр нүүрсний хулгайн асуудал шалгагдаж байгаа ба асуудал эцэслэгдэн шийдвэрлэгдээгүй байна.",
                "role_context": "ЦЕГ-ын мөрдөн шалгах ажиллагаа",
                "start_date": "2022-11-30",
                "tags": ["цег", "эдийн_засгийн_гэмт_хэрэг", "мөрдөн_байцаалт"],
            },
            {
                "entity_id": ett.id,
                "fact_type": "chronological",
                "fact": "Нүүрс тээвэрт тээврийн хэрэгслийн дугаар нь өөрчлөгдсөн, хоосон гэж мэдүүлсэн хэрнээ нүүрс ачиж хилээр гарсан асуудлыг хууль хяналтын байгууллагууд шалгаж эхэлсэн.",
                "source_quote": "Нөгөө талдаа дугаар нь өөрчлөгдсөн, хоосон гэж мэдүүлсэн хэрнээ нүүрс ачиж гарсан асуудал хүртэл үүнийг дагаад бий болж байгаа. Уг асуудалтай холбоотой хяналт шалгалтын үйл ажиллагаа хууль хяналтын байгууллагуудад явагдаж байгаа.",
                "role_context": "Бүртгэлгүй тээвэрлэлтийн зөрчил",
                "start_date": "2022-11-30",
                "tags": ["хоосон_мэдүүлэг", "хуурамч_дугаар", "тээвэр"],
            }
        ]

        for item in facts_2qfn:
            verify_substring(item["source_quote"], src_2qfn.selected_text, item["fact"][:30])
            ex = db.query(models.Fact).filter(
                models.Fact.source_id == src_2qfn.id,
                models.Fact.source_quote == item["source_quote"]
            ).first()
            if not ex:
                f_date, precision, date_end = parse_flexible_date(item["start_date"]) if item.get("start_date") else (None, None, None)
                f = models.Fact(
                    entity_id=item["entity_id"],
                    source_id=src_2qfn.id,
                    fact_type=item["fact_type"],
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    fact_date=f_date,
                    date_precision=precision,
                    fact_date_end=date_end,
                    sentiment_score=-0.5,
                )
                f.tags = item.get("tags", [])
                db.add(f)
                importing.assign_fact_id(db, f)
                link_case_fact(db, case_id, f.id, "EVIDENCE_FOR", item.get("role_context"))
                print(f"Added fact: {f.fact_id}")

        # -------------------------------------------------------------
        # Source 12: news_2694237 (Тойм 2023: Онцлох үйл явдлууд)
        # -------------------------------------------------------------
        url_2694237 = "https://news.mn/r/2694237/"
        src_news = db.query(models.Source).filter(models.Source.url == url_2694237).first()
        scraped_news = scraper.scrape(url_2694237)
        blocks_news = [
            b["text"].strip() for b in scraped_news.get("blocks", [])
            if len(b["text"].strip()) > 10
            and not b["text"].startswith("Хуучирсан мэдээ:")
            and not b["text"].startswith("News.MN")
        ]
        text_news = "\n\n".join(blocks_news)
        if not src_news:
            src_news = models.Source(
                source_type="article",
                category="media",
                url=url_2694237,
                title="Тойм 2023: Монгол Улсад болсон онцлох 5 үйл явдлыг нэрлэж байна | News.MN",
                author="News.MN",
                publication_date=parse_flexible_date("2023-12-26")[0],
                cleaned_text=text_news,
                selected_text=text_news,
                raw_hash=stable_hash(text_news),
                sha256_hash=stable_hash(text_news),
                bias_score=0.9,
                reliability_score=0.9,
            )
            db.add(src_news)
            db.flush()
            print(f"Created Source: {src_news.title} (id={src_news.id})")
        else:
            print(f"Existing Source: {src_news.title} (id={src_news.id})")

        facts_news = [
            {
                "entity_id": ett.id,
                "fact_type": "chronological",
                "fact": "2023 онд болсон нүүрсний нээлттэй сонсголоор 'Эрдэнэс Тавантолгой' төрийн өмчит компаниас нийтдээ 5.2 сая тонн нүүрс бүртгэлгүй гарсан асуудлыг хоёр үе шаттай сонсголоор хэлэлцсэн.",
                "source_quote": "Нэг тонн, нэг мянган тонн биш нийтдээ 5.2 сая тонн нүүрс бүртгэлгүй гарсныг нээлттэй сонсголоор хөндсөн юм.",
                "role_context": "2023 оны онцлох үйл явдал: Сонсгол ба 5.2 сая тонн",
                "start_date": "2023-12-26",
                "tags": ["сонсгол", "5.2_сая_тонн", "2023_онцлох"],
            },
            {
                "entity_id": ett.id,
                "fact_type": "chronological",
                "fact": "Нүүрсний хулгайн нээлттэй сонсголыг хоёр үе шаттай явуулсан бөгөөд төрийн өмчит 'Эрдэнэс Тавантолгой' компани дээр гарсан хэрэг явдал хамгийн их анхаарал татсан.",
                "source_quote": "Нүүрсний хулгайн нээлттэй сонсголыг хоёр үе шаттай явуулсан агаад хамгийн их анхаарал татсан нь төрийн өмчит “Эрдэнэс Тавантолгой” дээр гарсан хэрэг, явдал.",
                "role_context": "Нээлттэй сонсголын үе шат",
                "start_date": "2023-12-26",
                "tags": ["хоёр_үе_шат", "этт", "сонсгол"],
            }
        ]

        for item in facts_news:
            verify_substring(item["source_quote"], src_news.selected_text, item["fact"][:30])
            ex = db.query(models.Fact).filter(
                models.Fact.source_id == src_news.id,
                models.Fact.source_quote == item["source_quote"]
            ).first()
            if not ex:
                f_date, precision, date_end = parse_flexible_date(item["start_date"]) if item.get("start_date") else (None, None, None)
                f = models.Fact(
                    entity_id=item["entity_id"],
                    source_id=src_news.id,
                    fact_type=item["fact_type"],
                    fact_text=item["fact"],
                    source_quote=item["source_quote"],
                    role_context=item.get("role_context"),
                    fact_date=f_date,
                    date_precision=precision,
                    fact_date_end=date_end,
                    sentiment_score=-0.5,
                )
                f.tags = item.get("tags", [])
                db.add(f)
                importing.assign_fact_id(db, f)
                link_case_fact(db, case_id, f.id, "EVIDENCE_FOR", item.get("role_context"))
                print(f"Added fact: {f.fact_id}")

        db.commit()
        print("Done ingesting additional coal facts!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
