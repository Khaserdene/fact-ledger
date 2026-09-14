# -*- coding: utf-8 -*-
"""УИХ 1992–1996 — анхны УИХ-ын сонгуулийн фактууд болон гишүүдийг холбох."""
import json
import urllib.request

API = "http://127.0.0.1:8020"


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


src = req("POST", "/sources", {
    "source_type": "article",
    "title": "1992 оны Улсын Их Хурлын сонгууль — Википедиа нэвтэрхий толь",
    "url": "https://mn.wikipedia.org/wiki/1992_оны_Улсын_Их_Хурлын_сонгууль",
    "selected_blocks": ["1992 оны Улсын Их Хурлын сонгууль нь Монгол Улсад 1992 оны 6-р сарын 28-нд явагдсан. УИХ-ын анхны сонгууль. 26 тойрогт 293 нэр дэвшигч өрсөлдсөн, нийт сонгогчдын 95.6% оролцов. МАХН 70, Ардчилсан холбоо 4, МСДН 1, бие даагч 1 суудал авсан."],
    "raw_text": "1992 оны Улсын Их Хурлын сонгууль нь Монгол Улсад 1992 оны 6-р сарын 28-нд явагдсан. УИХ-ын анхны сонгууль. 26 тойрогт 293 нэр дэвшигч өрсөлдсөн, нийт сонгогчдын 95.6% оролцов. МАХН 70, Ардчилсан холбоо 4, МСДН 1, бие даагч 1 суудал авсан.",
})
print("source:", src["id"])

p = {
    "article_id": src["id"],
    "new_chronological_facts": [
        {"date": "1992-06-28", "fact": "УИХ-ын анхны сонгууль явагдаж, томсгосон 26 тойрогт 10 нам, бие даагч нийлээд 293 нэр дэвшигч өрсөлдөв; нийт сонгогчдын 95.6% оролцов.",
         "source_quote": "Уг сонгууль нь УИХ-ын анхны сонгууль байсан. Сонгуулийн томсгосон 26 тойрогт 10 улс төрийн намаас болон бие даагч нийлээд 293 нэр дэвшигч өрсөлдсөн байна", "tags": ["сонгууль"]},
        {"date": "1992-07-01", "fact": "Суудлын хуваарилалт: МАХН 70, «Ардчилсан холбоо» эвсэл (МоАН, МҮДН, МНН) 4, МСДН 1, бие даагч 1 суудал.",
         "source_quote": "Монгол Ардын Хувьсгалт Нам 70, Монголын Ардчилсан Нам, Монголын Үндэсний Дэвшлийн Нам, Монголын Нэгдсэн Намын \"Ардчилсан холбоо\" эвсэл 4, Монголын Социал-Демократ Нам 1, бие даан нэр дэвшигч 1 суудал", "tags": ["сонгууль", "суудал"]},
        {"date": "1992-07", "fact": "УИХ-ын хамгийн олон суудал авсан МАХН-аас Нацагийн Багабандийг УИХ-ын дарга, Жамбын Гомбожавыг дэд даргаар сонгожээ.",
         "source_quote": "МАХН-аас Улсын Их Хурлын даргаар Нацагийн Багабандийг, дэд даргаар Жамбын Гомбожавыг сонгожээ", "tags": ["УИХ"]},
        {"date": "1992", "fact": "Өмнөх Улсын Бага Хурлын 50 гишүүнээс 15 хүнийг энэ анхны УИХ-д улиран сонгосон.",
         "source_quote": "Өмнөх 1990-1992 оны Улсын Бага Хурлын гишүүдээс 15 хүнийг энэхүү анхны УИХ-д улираан сонгосон түүхтэй", "tags": ["сонгууль"]},
    ],
    "new_biographical_facts": [],
    "new_relationships": [],
    "contradictions_detected": [],
}
print(json.dumps(req("POST", "/entities/47/import-facts", p), ensure_ascii=False))

# Гишүүдийг холбох: Багабанди (байгаа), Элбэгдорж (1992-1996 дутуу), Ж.Гомбожав (шинэ stub)
ents = {e["name"].lower(): e["id"] for e in req("GET", "/entities")}

# Ж.Гомбожав — УИХ-ын дэд дарга
gid = ents.get("жамбын гомбожав")
if not gid:
    e = req("POST", "/entities", {
        "name": "Жамбын Гомбожав", "entity_type": "person",
        "description": "УИХ-ын дэд дарга (1992). 1992 оны анхны УИХ-ын сонгуулиар МАХН-аас сонгогдсон.",
    })
    gid = e["id"]
    print("new entity:", gid, e["name"])

# 47 руу холбох хүмүүс
for pid, rel_type in [
    (gid, "УИХ-ын гишүүн, дэд дарга"),
    (ents.get("нацагийн багабанди", 1), "УИХ-ын гишүүн, дарга"),
    (ents.get("цахиагийн элбэгдорж", 12), "УИХ-ын гишүүн"),
]:
    if not pid:
        continue
    already = any(r["target_entity_id"] == 47 for r in req("GET", f"/entities/{pid}/relationships"))
    if already:
        print("  already linked:", pid)
        continue
    rel = req("POST", "/relationships", {
        "source_entity_id": pid, "target_entity_id": 47,
        "rel_type": rel_type, "start_date_input": "1992-07-01", "end_date_input": "1996-07-01",
    })
    print("  linked", pid, "->", rel.get("id"))
print("DONE")
