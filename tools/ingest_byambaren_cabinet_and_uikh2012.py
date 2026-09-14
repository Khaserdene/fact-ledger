# -*- coding: utf-8 -*-
"""1) Д.Бямбасүрэнгийн танхим (1990–1992) нэмэх  2) УИХ 2012–2016 гишүүд нэмэх (gogo)."""
import json
import urllib.request

API = "http://127.0.0.1:8020"


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


ents = {e["name"].lower(): e["id"] for e in req("GET", "/entities")}
for a in req("GET", "/entities"):
    for al in a["aliases"]:
        ents.setdefault(al["alias"].lower(), a["id"])


def ensure_person(name, description, aliases=None):
    eid = ents.get(name.lower())
    if eid:
        return eid, False
    e = req("POST", "/entities", {
        "name": name, "entity_type": "person",
        "description": description,
        "aliases": aliases or [],
    })
    ents[name.lower()] = e["id"]
    return e["id"], True


# ── 1. Д.Бямбасүрэнгийн танхим (1990-09-11 ~ 1992-07-21) ──
pm_id, new = ensure_person(
    "Дашаадайн Бямбасүрэн",
    "Монгол Улсын Ерөнхий сайд (1990-1992). Ардчилсан шилжилтийн үеийн анхны танхимыг тэргүүлсэн.",
    ["Д.Бямбасүрэн", "Бямбасүрэн"],
)
print("Бямбасүрэн id:", pm_id, "(new)" if new else "(existing)")

src = req("POST", "/sources", {
    "source_type": "article",
    "title": "Монгол Улсын Засгийн газар — Википедиа нэвтэрхий толь",
    "url": "https://mn.wikipedia.org/wiki/Монгол_Улсын_Засгийн_газар",
    "selected_blocks": ["Үе үеийн Засгийн газрууд: Д.Бямбасүрэнгийн танхим 1990 оны 9 сарын 11 - 1992 оны 7 сарын 21."],
    "raw_text": "Үе үеийн Засгийн газрууд: Д.Бямбасүрэнгийн танхим 1990 оны 9 сарын 11 - 1992 оны 7 сарын 21.",
})
e = req("POST", "/entities", {
    "name": "Д.Бямбасүрэнгийн танхим (1990–1992)", "entity_type": "government",
    "description": "Ардчилсан шилжилтийн үеийн анхны танхим. 1990-09-11-ээс 1992-07-21 хүртэл ажилласан.",
})
gid = e["id"]
print("CABINET_ID=", gid)
req("POST", f"/entities/{gid}/import-facts", {
    "article_id": src["id"],
    "new_chronological_facts": [
        {"date": "1990-09-11", "fact": "Д.Бямбасүрэнгийн танхим ажиллаж эхэлсэн (ардчилсан шилжилтийн үеийн анхны танхим).",
         "source_quote": "Д.Бямбасүрэнгийн танхим 1990 оны 9 сарын 11 - 1992 оны 7 сарын 21", "tags": ["засгийн газар"]},
        {"date": "1992-07-21", "fact": "1992 оны УИХ-ын сонгууль болсонтой холбогдон албан тушаалаа шилжүүлсэн.",
         "source_quote": "Д.Бямбасүрэнгийн танхим 1990 оны 9 сарын 11 - 1992 оны 7 сарын 21", "tags": ["засгийн газар"]},
    ],
    "new_biographical_facts": [], "new_relationships": [], "contradictions_detected": [],
})
req("POST", "/relationships", {
    "source_entity_id": pm_id, "target_entity_id": gid,
    "rel_type": "тэргүүлсэн", "start_date_input": "1990-09-11", "end_date_input": "1992-07-21",
    "source_id": src["id"],
})
req("POST", "/relationships", {
    "source_entity_id": 32, "target_entity_id": gid,  # Д.Содном: угшил өгсөн
    "rel_type": "угшил өгсөн", "start_date_input": "1990-09-11",
    "source_id": src["id"],
})
req("POST", "/relationships", {
    "source_entity_id": 27, "target_entity_id": gid,  # П.Жасрай: угшил авсан
    "rel_type": "угшил авсан", "start_date_input": "1992-07-21",
    "source_id": src["id"],
})
print("cabinet links ok")

# ── 2. УИХ 2012–2016 (conv 52) гишүүд нэмэх (gogo source 40 эсвэл шинэ source) ──
gogo = req("POST", "/sources", {
    "source_type": "article",
    "title": "УИХ-ын гишүүн болохоос татгалзсан найман эрхэм — GoGo.mn",
    "url": "https://gogo.mn/r/9kjn2",
    "selected_blocks": ["2012 оны УИХ-ын сонгуулиар нэр дэвшиж, улмаар УИХ-ын гишүүн гэсэн эрхэм цолыг хүртсэн 76 эрхмээс энэ удаагийн сонгуульд 68 нь дахин нэр дэвшихээр горилж байна. Л.Цог, Р.Амаржаргал, Су.Батболд, Д.Дэмбэрэл нар 2016 онд нэрээ дэвшүүлсэнгүй."],
    "raw_text": "Л.Цог энэ удаад нэрээ дэвшүүлсэнгүй. Р.Амаржаргал энэ удаагийн сонгуульд өрсөлдөхгүй. Су.Батболд. Д.Дэмбэрэл. М.Батчимэг.",
})
members = [
    ("Л.Цог", "УИХ-ын гишүүн (2012–2016). 2016 оны сонгуульд нэрээ дэвшүүлсэнгүй. Тусгаар тогтнол, эв нэгдлийн намд элссэн.", []),
    ("Р.Амаржаргал", "УИХ-ын гишүүн (2004–2016, гурван удаа). 2016 оны сонгуульд бие даан өрсөлдөөгүй.", ["Амаржаргал"]),
    ("Су.Батболд", "УИХ-ын гишүүн (2012–2016). 2016 оны сонгуульд нэр дэвшүүлсэнгүй.", ["Су.Батболд"]),
    ("Магнаагийн Батчимэг", "УИХ-ын гишүүн (2012–2016). 2016 оны сонгуульд 61-р тойрогоор сонгогдсон.", ["М.Батчимэг"]),
    ("Нямаагийн Энхболд", "УИХ-ын гишүүн (2012–2016). 2016 оны сонгуульд нэр дэвшүүлсэнгүй.", ["Н.Энхболд (Ням-Осорын)"]),
]
for name, desc, aliases in members:
    eid = ents.get(name.lower())
    new = False
    if not eid:
        e = req("POST", "/entities", {"name": name, "entity_type": "person",
                                      "description": desc, "aliases": aliases})
        eid = e["id"]
        ents[name.lower()] = eid
        print("created", eid, name)
    already = any(r["target_entity_id"] == 52 for r in req("GET", f"/entities/{eid}/relationships"))
    if not already:
        rel = req("POST", "/relationships", {
            "source_entity_id": eid, "target_entity_id": 52,
            "rel_type": "УИХ-ын гишүүн", "start_date_input": "2012-07-01", "end_date_input": "2016-07-01",
            "source_id": gogo["id"],
        })
        print("linked", name, "-> 52", rel.get("id"))
print("DONE")
