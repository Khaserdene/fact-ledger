# -*- coding: utf-8 -*-
"""Ж.Эрдэнэбатын Засгийн газар (2016–2017) — дутуу ЗГ-ийн холбоосыг нөхөх."""
import json
import re
import urllib.parse
import urllib.request

from ingest_ministers import API, api_req, parse_ministers, wiki_wikitext


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


wt = wiki_wikitext("Жаргалтулгын Эрдэнэбатын Засгийн газар")
src = req("POST", "/sources", {
    "source_type": "article",
    "title": "Жаргалтулгын Эрдэнэбатын Засгийн газар — Википедиа нэвтэрхий толь",
    "url": "https://mn.wikipedia.org/wiki/Жаргалтулгын_Эрдэнэбатын_Засгийн_газар",
    "selected_blocks": ["Ж.Эрдэнэбатын Засгийн газар 2016 оны 7 сарын 7-нд бүрдэж, 2017 оны 10 сарын 4 хүртэл ажилласан. МАХН-ын давамгайлсан бүрэлдэхүүнтэй."],
    "raw_text": "Ж.Эрдэнэбатын Засгийн газар 2016 оны 7 сарын 7-нд бүрдэж, 2017 оны 10 сарын 4 хүртэл ажилласан. МАХН-ын давамгайлсан бүрэлдэхүүнтэй.",
})
print("source:", src["id"])

ents = {e["name"].lower(): e["id"] for e in api_req("GET", "/entities")}
pm_id = ents.get("жаргалтулгын эрдэнэбат")
print("PM entity:", pm_id)

# ЗГ entity үүсгэх
e = req("POST", "/entities", {
    "name": "Ж.Эрдэнэбатын Засгийн газар (2016–2017)", "entity_type": "government",
    "description": "МАХН-ын давамгайлсан Засгийн газар. 2016-07-07-нд бүрдэж, 2017-10-04 хүртэл ажилласан.",
})
gid = e["id"]
print("CABINET_ID=", gid)

p = {
    "article_id": src["id"],
    "new_chronological_facts": [
        {"date": "2016-07-07", "fact": "МАХН-ын давамгайлсан бүрэлдэхүүнтэй Ж.Эрдэнэбатын Засгийн газар бүрдсэн.",
         "source_quote": "Ж.Эрдэнэбатын тэргүүлсэн Засгийн газар бүрдлээ", "tags": ["засгийн газар"]},
        {"date": "2017-10-04", "fact": "Засгийн газар бүрэн эрхээ дуусгаад, оронд нь Ухнаагийн Хүрэлсүхийн Засгийн газар байгуулагдсан.",
         "source_quote": "2017 оны 10 сарын 4", "tags": ["засгийн газар"]},
    ],
    "new_biographical_facts": [],
    "new_relationships": [],
    "contradictions_detected": [],
}
print(json.dumps(req("POST", f"/entities/{gid}/import-facts", p), ensure_ascii=False))

# PM тэргүүлсэн холбоос
req("POST", "/relationships", {
    "source_entity_id": pm_id, "target_entity_id": gid,
    "rel_type": "тэргүүлсэн", "start_date_input": "2016-07-07", "end_date_input": "2017-10-04",
    "source_id": src["id"],
})
# намын холбоос
req("POST", "/relationships", {
    "source_entity_id": 7, "target_entity_id": gid,
    "rel_type": "олонх буюу эвслийн нам", "start_date_input": "2016", "end_date_input": "2017",
    "source_id": src["id"],
})

# Сайд нарыг оруулах (Ерөнхий сайд мөрөөр алгасана — PM өөрөө аль хэдийн холбогдсон)
ministers = [m for m in parse_ministers(wt) if "Ерөнхий сайд" not in m[1]]
print("ministers parsed:", len(ministers))
name2id = {"Ухнаагийн Хүрэлсүх": 14, "Бадмаанямбуугийн Бат-Эрдэнэ": 21}
for n, ministry in ministers:
    eid = ents.get(n.lower())
    if not eid:
        e = req("POST", "/entities", {
            "name": n, "entity_type": "person",
            "description": f"{ministry} (Ж.Эрдэнэбатын Засгийн газар)",
        })
        eid = e["id"]
        ents[n.lower()] = eid
    rel = req("POST", "/relationships", {
        "source_entity_id": eid, "target_entity_id": gid,
        "rel_type": f"сайд ({ministry})", "source_id": src["id"],
    })
print("DONE", gid)
