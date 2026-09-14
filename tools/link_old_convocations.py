# -*- coding: utf-8 -*-
"""Хуучин тойргууд (46,47,48,49,50,52) — фактууд дээр үндэслэн гишүүдийг холбох.

Шилжилтийн үе (1990-1992): АИХ депутат / Бага Хурлын гишүүн мөрүүд.
1992-2008: УИХ гишүүнчлэлийн огноо давхцсан фактууд.
"""
import json
import re
import urllib.request

API = "http://127.0.0.1:8020"

CONVOS = [
    (46, 1990, 1992, "АИХ-ын депутат / Улсын Бага Хурлын гишүүн (шилжилтийн үе)"),
    (47, 1992, 1996, "УИХ-ын гишүүн"),
    (48, 1996, 2000, "УИХ-ын гишүүн"),
    (49, 2000, 2004, "УИХ-ын гишүүн"),
    (50, 2004, 2008, "УИХ-ын гишүүн"),
    (52, 2012, 2016, "УИХ-ын гишүүн"),
]


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


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
    existing = {r["target_entity_id"] for r in req("GET", f"/entities/{pid}/relationships")}
    matched = {}  # conv_id -> (rel_type, evidence)
    for f in facts:
        t = f["fact_text"]
        low = t.lower()
        if not any(k in low for k in ("аих", "ардын их хурал", "бага хурал", "уих", "их хурлын гишүүн", "улсын их хурал")):
            continue
        if not any(k in low for k in ("гишүүн", "депутат", "дарга")):
            continue
        # тухайн фактын жилүүд
        years = set()
        if f.get("fact_date"):
            years.add(int(str(f["fact_date"])[:4]))
        if f.get("fact_date_end"):
            years.add(int(str(f["fact_date_end"])[:4]))
        for m in re.finditer(r"(19|20)(\d{2})", t):
            years.add(int(m.group(0)))
        years.discard(None)
        for cid, cf, ct, rtype in CONVOS:
            if cid in existing:
                continue
            # фактын жилүүдийн аль нэг нь тойргийн хугацаанд орвол
            if any(cf <= y <= ct for y in years):
                matched.setdefault(cid, (rtype, t[:70]))
    for cid, (rtype, evidence) in matched.items():
        rel = req("POST", "/relationships", {
            "source_entity_id": int(pid), "target_entity_id": cid,
            "rel_type": rtype,
        })
        created += 1
        print(f"  {id2name[pid][:28]:28} -> УИХ {cid} | {evidence[:50]}")

print("created:", created)
