# -*- coding: utf-8 -*-
"""Хүрэлсүх — GoGo хоёр дахь эх сурвалж + зөрчил бүртгэл."""
import json
import urllib.request

API = "http://127.0.0.1:8020"


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


payload = {
    "article_id": 40,
    "new_biographical_facts": [
        {"fact": "Англи, Орос хэлтэй.",
         "source_quote": "Англи, Орос хэл", "tags": ["боловсрол"]},
    ],
    "new_chronological_facts": [
        {"date": "1996-1997", "fact": "МАХН-ын Залуучууд Хөгжил төвийн Ерөнхий захирлаар ажилласан.",
         "source_quote": "1996-1997 онд МАХН-ын Залуучууд Хөгжил төвийн Ерөнхий захирал", "tags": ["карьер"]},
        {"date": "2000-2007", "fact": "МАХН-ын Удирдах Зөвлөлийн гишүүн байсан.",
         "source_quote": "2000-2007 онд МАХН-ын Удирдах Зөвлөлийн гишүүн", "tags": ["улс төр"]},
        {"date": "2016-07", "fact": "Засгийн газрын гишүүн, Монгол Улсын Шадар сайдаар хоёр дахь удаагаа томилогдсон.",
         "source_quote": "2016 оноос Засгийн газрын гишүүн, Монгол Улсын Шадар сайд", "tags": ["сайд"]},
        {"date": "2021-06", "fact": "2021 оны ерөнхийлөгчийн сонгуулийн урьдчилсан дүнгээр МАН-ын нэр дэвшигч У.Хүрэлсүх олонхийн санал буюу 67 орчим хувийн санал авчээ (сонгуулийн албан ёсны дүн тухайн үед гараагүй).",
         "source_quote": "МАН-аас нэр дэвшигч У.Хүрэлсүх олонхийн санал буюу 67 орчим хувийн санал аваад байна", "tags": ["ерөнхийлөгч", "сонгууль"]},
    ],
    "new_relationships": [],
    "contradictions_detected": [
        {"new_fact_quote": "МАН-аас нэр дэвшигч У.Хүрэлсүх олонхийн санал буюу 67 орчим хувийн санал аваад байна",
         "contradicted_fact_id": "F278",
         "reason": "2021 оны ерөнхийлөгчийн сонгуулийн дүнгийн хувь зөрүүтэй: Википедиа (source 34) 72.02% / 823,326 санал гэж өгсөн бол GoGo.mn (source 40) урьдчилсан дүнгээр 67 орчим хувь гэж бичсэн (албан ёсны дүн тухайн нийтлэлийн үед гараагүй)."},
    ],
}
print(json.dumps(req("POST", "/entities/14/import-facts", payload), ensure_ascii=False))
