# -*- coding: utf-8 -*-
"""УИХ-ын бүрэн эрхийн тойргуудыг субъект болгох."""
import json
import urllib.request

API = "http://127.0.0.1:8020"

def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


# (нэр, from, to, дүр, сонгуулийн он, суудлын тоо, тайлбар)
CONVOCATIONS = [
    ("УИХ 1990–1992 (Шилжилтийн)", "1990-09-01", "1992-07-01", 1990, None,
     "Ардчилсан хувьсгалын дараах шилжилтийн үе: Ардын Их Хурал ба Улсын Бага Хурал хамтран, шинэ Үндсэн хууль баталсан."),
    ("УИХ 1992–1996", "1992-07-01", "1996-07-01", 1992, 76,
     "Шинэ Үндсэн хуулийн дагуу байгуулагдсан анхны УИХ; МАХН давамгайлсан."),
    ("УИХ 1996–2000", "1996-07-01", "2000-07-01", 1996, 76,
     "Ардчилсан Холбоо Эвсэл түүхэн ялалт байгуулсан тойрог."),
    ("УИХ 2000–2004", "2000-07-01", "2004-07-01", 2000, 76,
     "МАХН 72 суудал авч давамгайлсан тойрог."),
    ("УИХ 2004–2008", "2004-07-01", "2008-07-01", 2004, 76,
     "АН-МАХН тэнцүү суудал авсан, Их эвслийн засгийн газартай болсон тойрог."),
    ("УИХ 2008–2012", "2008-07-01", "2012-07-01", 2008, 76,
     "МАХН 41, АН 27 суудал авсан; 7-1-ний үймээн дараа нь хамтарсан засгийн газартай болсон."),
    ("УИХ 2012–2016", "2012-07-01", "2016-07-01", 2012, 76,
     "АН хамгийн олон суудал авч Шинэчлэлийн Засгийн газрыг байгуулсан тойрог."),
    ("УИХ 2016–2020", "2016-07-01", "2020-07-01", 2016, 76,
     "МАН 65 суудал авч давамгайлсан тойрог."),
    ("УИХ 2020–2024", "2020-07-01", "2024-07-01", 2020, 76,
     "МАН 62 суудал авсан; COVID-19-ийн онцгой байдлын үетэй давхцсан тойрог."),
    ("УИХ 2024–2028", "2024-07-01", "2028-07-01", 2024, 126,
     "Үндсэн хуулийн нэмэлт өөрчлөлтийн дагуу анхны 126 суудалтай, 4 жилийн бүрэн эрхтэй тойрог."),
]

created = {}
for name, fr, to, year, seats, desc in CONVOCATIONS:
    facts = [
        {"date": f"{year}-06-01", "fact": f"{year} оны Улсын Их Хурлын сонгууль явагдаж, энэ тойрог бүрэн эрхээ хэрэгжүүлж эхэлсэн.",
         "source_quote": None, "tags": ["сонгууль"]},
    ]
    if seats:
        facts.append({"date": fr, "fact": f"Нийт {seats} суудалтай бүрэн эрхийн тойрог.",
                      "source_quote": None, "tags": ["суудал"]})
    e = req("POST", "/entities", {
        "name": name, "entity_type": "parliament",
        "description": f"Улсын Их Хурлын {year} оны сонгуулиар бүрэлдэхүүнээ тогтоосон тойрог. {desc}",
    })
    pid = e["id"]
    p = {"article_id": None, "new_chronological_facts": facts, "new_biographical_facts": [],
         "new_relationships": [], "contradictions_detected": []}
    print(name, "->", pid, json.dumps(req("POST", f"/entities/{pid}/import-facts", p), ensure_ascii=False))
    created[name] = pid

print("CREATED:", json.dumps(created, ensure_ascii=False))
