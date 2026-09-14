# -*- coding: utf-8 -*-
"""УИХ-ын жагсаалтын вики-хуудаснаас гишүүдийг задлан субъект + холбоос үүсгэх.

Хэрэглээ: python ingest_uikh_members.py "<конво_id>" "<вики хуудасны нэр>" "<from>" "<to>"
Жишээ: python ingest_uikh_members.py 54 "Улсын Их Хурлын гишүүдийн жагсаалт, 2020–2024" 2020-07-02 2024-07-03
"""
import json
import re
import sys
import urllib.parse
import urllib.request

API = "http://127.0.0.1:8020"
WIKI_API = "https://mn.wikipedia.org/w/api.php"


def api_req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


def fetch_wikitext(title):
    url = ("https://mn.wikipedia.org/w/api.php?action=parse&page="
           + urllib.parse.quote(title) + "&prop=wikitext&format=json&redirects=1")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fact-ledger"})) as r:
        d = json.load(r)
    return d["parse"]["wikitext"]["*"]


def clean(t):
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<font[^>]*>|</font>", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", t)
    return t.strip()


def parse_members(wikitext):
    """Бүх хүснэгтийг cell түвшинд задалж (нэр, нам) хосыг гаргана."""
    wt = re.sub(r"<ref[^>]*/>", "", wikitext)
    wt = re.sub(r"<ref[^>]*>.*?</ref>", "", wt, flags=re.S)

    BAD_IN_NAME = ("тойрог", "Нам", "Эвсэл", "сонгууль", "Ордон", "хүртэл", "хойш",
                   "style", "scope", "rowspan", "colspan", "width")

    PARTY_MAP = {"АН": "Ардчилсан Нам", "МАХН": "Монгол Ардын Хувьсгалт Нам",
                 "МАН": "Монгол Ардын Нам", "МҮАН": "Монгол Үндэсний Ардчилсан Нам",
                 "ХҮН": "Зөв Хүн Электорат Эвсэл"}

    def is_name(c):
        return (5 <= len(c) <= 55 and " " in c and not re.search(r"\d", c)
                and not any(b in c for b in BAD_IN_NAME))

    def is_party(c):
        if re.search(r"\d|[={]", c):
            return False
        if c in PARTY_MAP:
            return True
        return 2 <= len(c) <= 60 and (c.endswith("Нам") or c.endswith("Эвсэл") or c in ("ХҮН", "бие даагч"))

    def canonical_name(raw_cell, cleaned):
        # [[Төрх|Лейбл]] байвал Төрх (бүтэн нэр) нь canonical
        m = re.search(r"\[\[([^|\]]+)\|", raw_cell)
        if m:
            return m.group(1).strip()
        return cleaned

    def canon_party(cleaned):
        return PARTY_MAP.get(cleaned, cleaned)

    members, seen = [], set()
    for tb in re.findall(r"\{\|(.*?)\n\|\}", wt, flags=re.S):
        for row in re.split(r"\n\|-\n?", tb):
            if "<s>" in row:
                row = re.sub(r"<s>.*?</s>", "", row, flags=re.S)
            raw_cells, cells = [], []
            for line in row.split("\n"):
                if line.strip().startswith(("!", "{|", "|}")):
                    continue  # header болон хүснэгтийн шинж чанарын мөр
                for part in line.split("||"):
                    part = part.strip()
                    if part.startswith("|"):
                        part = re.sub(r"^\|+\s*(?:rowspan\s*=\s*\d+\s*)?\|*", "", part).strip()
                    if not part:
                        continue
                    raw_cells.append(part)
                    c0 = clean(part)
                    # style="..." |<content> хэлбэр бол сүүлийн pipe-ээс хойшхийг авах
                    if "=" in c0 and "|" in c0:
                        c0 = c0.rsplit("|", 1)[-1].strip()
                    cells.append(c0)
            for i, c in enumerate(cells):
                if is_party(c):
                    for j in range(i - 1, max(-1, i - 5), -1):
                        if is_name(cells[j]):
                            cname = canonical_name(raw_cells[j], cells[j])
                            key = cname.lower()
                            if key not in seen:
                                seen.add(key)
                                members.append((cname, canon_party(c)))
                            break
    return members


def main():
    conv_id = sys.argv[1]
    title = sys.argv[2]
    date_from = sys.argv[3]
    date_to = sys.argv[4]

    wt = fetch_wikitext(title)
    members = parse_members(wt)
    print(f"parsed {len(members)} members from: {title}")

    existing = {}
    for e in api_req("GET", "/entities"):
        existing[e["name"].lower()] = e["id"]
        for a in e["aliases"]:
            existing.setdefault(a["alias"].lower(), e["id"])

    created = reused = linked = skipped = 0
    seen = set()
    for name, party in members:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        eid = existing.get(key)
        if eid:
            reused += 1
        else:
            e = api_req("POST", "/entities", {
                "name": name, "entity_type": "person",
                "description": f"УИХ-ын гишүүн ({title}), {party}",
                "aliases": [],
            })
            eid = e["id"]
            existing[key] = eid
            created += 1
        # давхар холбоосоос сэргийлэх
        already = any(r["target_entity_id"] == int(conv_id)
                      for r in api_req("GET", f"/entities/{eid}/relationships"))
        if already:
            skipped += 1
            continue
        api_req("POST", "/relationships", {
            "source_entity_id": eid, "target_entity_id": int(conv_id),
            "rel_type": f"УИХ-ын гишүүн ({party})",
            "start_date_input": date_from, "end_date_input": date_to,
        })
        linked += 1
    print(f"created={created} reused={reused} linked={linked} skipped_dupes={skipped}")


if __name__ == "__main__":
    main()
