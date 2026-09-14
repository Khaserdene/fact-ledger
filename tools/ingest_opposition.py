# -*- coding: utf-8 -*-
"""Кабинет бүрд олонх/сөрөг хүчний улс төрчдийг холбох.

Логик:
- ЗГ бүрийн "олонх буюу эвслийн нам" холбоосоос засгийн эрхийн нам тогтооно.
- Хүн бүрийн намын гишүүнчлэл/удирдлагын холбоосоор намыг нь тогтоож,
  ЗГ-ийн намтай нь ижил бол ОЛОНХ, өөр бол СӨРӨГ ХҮЧИН гэж ангилна.
- Хугацаа: ЗГ-ийн хугацаа ∩ хүний идэвхийн хугацаа (active_from/to) давхцвал л бүртгэнэ.
"""
import json
import urllib.request

API = "http://127.0.0.1:8020"
PARTY_IDS = {6, 7, 9}


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


graph = req("GET", "/graph")
nodes = {n["id"]: n for n in graph["nodes"]}
rels = graph["edges"]

# ЗГ-үүд
cabins = {n["id"]: n for n in graph["nodes"] if n.get("entity_type") == "government"}

# ЗГ бүрийн засгийн эрхийн нам (олонх буюу эвслийн нам холбоосоор)
cabinet_party = {}
cabinet_pm = {}
for e in rels:
    t = e["target"]
    if t in cabins:
        s = e["source"]
        if s in {str(p) for p in PARTY_IDS}:
            cabinet_party[t] = s
        else:
            n = nodes.get(s, {})
            if n.get("entity_type") == "person":
                cabinet_pm[t] = s

# Хүн бүрийн нам (намтай холбоосоор; хугацаатай эсэхээс үл хамааран)
person_party = {}  # person_id -> (party_id, examples)
for e in rels:
    s, t = e["source"], e["target"]
    if t in {str(p) for p in PARTY_IDS} and nodes.get(s, {}).get("entity_type") == "person":
        person_party.setdefault(s, t)

created = 0
for cid, cab in cabins.items():
    party = cabinet_party.get(cid)
    pm = cabinet_pm.get(cid)
    cfrom = cab.get("active_from")
    cto = cab.get("active_to")
    src_facts = None  # source_id relationships-ээс олохгүй бол null
    if not party:
        print("нам олдсонгүй:", cab["name"])
        continue
    for pid_s, person in nodes.items():
        if pid_s == pm or person.get("entity_type") != "person":
            continue
        pp = person_party.get(pid_s)
        if not pp or pp == party:
            continue  # намтай холбоогүй эсвэл өөрөө олонхын ЗГ-ийн толгой
        # давхцах хугацаа
        pfrom = person.get("active_from")
        pto = person.get("active_to")
        s_from = max(pfrom, cfrom) if (pfrom and cfrom) else (pfrom or cfrom)
        s_to = min(pto, cto) if (pto and cto) else (pto or cto)
        if s_from and s_to and s_from > s_to:
            continue
        # олонхын нам биш хүн → сөрөг хүчин
        rel_type = f"сөрөг хүчний улс төрч ({nodes[str(party)]['name']})"
        rel = req("POST", "/relationships", {
            "source_entity_id": int(pid_s), "target_entity_id": int(cid),
            "rel_type": rel_type,
            "start_date_input": s_from, "end_date_input": s_to,
        })
        created += 1
        print(f"  {person['name'][:30]:30} -> {cab['name'][:34]:34} [{s_from}~{s_to}]")

print("created:", created)
