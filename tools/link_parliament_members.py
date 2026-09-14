# -*- coding: utf-8 -*-
"""УИХ гишүүнчлэлийн фактаас тойрог бүрийг тогтоож холбох (v2)."""
import json
import re
import urllib.request

API = "http://127.0.0.1:8020"


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


CONVOS = [
    (46, 1990, 1992), (47, 1992, 1996), (48, 1996, 2000), (49, 2000, 2004),
    (50, 2004, 2008), (51, 2008, 2012), (52, 2012, 2016), (53, 2016, 2020),
    (54, 2020, 2024), (55, 2024, 2028),
]


def convos_containing(year):
    return [cid for cid, cf, ct in CONVOS if cf <= year <= ct]


graph = req("GET", "/graph")
people = [n for n in graph["nodes"] if n.get("entity_type") == "person" and not n.get("ghost")]
id2name = {n["id"]: n["name"] for n in graph["nodes"]}

created = 0
for person in people:
    pid = person["id"]
    try:
        facts = req("GET", f"/entities/{pid}/facts")
    except Exception:
        continue
    convos = set()
    for f in facts:
        t = f["fact_text"]
        is_member_fact = ("гишүүн" in t) and ("УИХ" in t or "Их Хурал" in t or "Бага Хурал" in t)
        if not is_member_fact:
            continue
        # 1. Хугацааны муж: 1996-2000
        for m in re.finditer(r"(19|20)(\d{2})\s*[-–—~]\s*(19|20)(\d{2})", t):
            y1 = int(m.group(1) + m.group(2))
            y2 = int(m.group(3) + m.group(4))
            for cid, cf, ct in CONVOS:
                if y1 <= ct and y2 >= cf:
                    convos.add(cid)
        # 2. "Y оноос хойш N удаа" → N дараалсан тойрог
        m = re.search(r"(19|20)(\d{2})\s*оны?\s*(өмнө|хойш|эхнээс)[^0-9]{0,30}?(\d+)\s*удaa", t, re.I) or \
            re.search(r"(19|20)(\d{2})[^0-9]{0,20}(?:хойш|эхнээс)[^0-9]{0,30}?(\d+)\s*удaa", t, re.I)
        m2 = re.search(r"(19|20)(\d{2})\s*онаас\s*хойш\s*(\d+)\s*удаа", t)
        if m2:
            y = int(m2.group(1) + m2.group(2))
            n_terms = int(m2.group(3))
            starts = convos_containing(y)
            if starts:
                first = CONVOS.index([c for c in CONVOS if c[0] == starts[0]][0])
                for c in CONVOS[first:first + n_terms]:
                    convos.add(c[0])
        # 3. "Y оноос УИХ" / "Y оноос ... гишүүнээр сонгогдсон"
        for m in re.finditer(r"(19|20)(\d{2})\s*онаос[^0-9]{0,40}(УИХ|Их Хурал|гишүүнээр)", t):
            y = int(m.group(1) + m.group(2))
            convos.update(convos_containing(y))
        # 4. "Y онд ... УИХ-ын гишүүнээр сонгогдсон/томилогдсон"
        for m in re.finditer(r"(19|20)(\d{2})\s*онд[^0-9]{0,60}(УИХ|Их Хурал)[^0-9]{0,40}гишүүн", t):
            y = int(m.group(1) + m.group(2))
            convos.update(convos_containing(y))
        # 5. fact_date / fact_date_end талбарын жилүүд
        for d in (f.get("fact_date"), f.get("fact_date_end")):
            if d:
                convos.update(convos_containing(int(str(d)[:4])))
    if not convos:
        continue
    existing = {r["target_entity_id"] for r in req("GET", f"/entities/{pid}/relationships")}
    for cid, cf, ct in CONVOS:
        if cid in convos and cid not in existing:
            req("POST", "/relationships", {
                "source_entity_id": int(pid), "target_entity_id": cid,
                "rel_type": "УИХ-ын гишүүн",
                "start_date_input": f"{cf}", "end_date_input": f"{ct}",
            })
            created += 1
            print(f"  {id2name[pid][:28]:28} -> УИХ {cf}–{ct}")

print("created:", created)
