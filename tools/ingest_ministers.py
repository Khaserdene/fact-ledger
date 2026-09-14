# -*- coding: utf-8 -*-
"""ЗГ-ийн вики-хуудсуудаас сайд нарын жагсаалт оруулах (rate-limit tolerant).

Хэрэглээ: python ingest_ministers.py [start_index]
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "http://127.0.0.1:8020"

CANDIDATES = [
    ("Содномын Засгийн газар", ["Думаагийн Содномын Засгийн газар"]),
    ("Жасрайн Засгийн газар", ["Пунцагийн Жасрайн Засгийн газар"]),
    ("Энхсайханы Засгийн газар", ["Мэндсайханы Энхсайханы Засгийн газар"]),
    ("Элбэгдоржийн I Засгийн газар", ["Цахиагийн Элбэгдоржийн Засгийн газар"]),
    ("Энхбаярын Засгийн газар", ["Намбарын Энхбаярын Засгийн газар"]),
    ("Энхболдын Засгийн газар (Үндэсний эв нэгдэл)", ["Миеэгомбын Энхболдын Засгийн газар"]),
    ("Баярын Засгийн газар", ["Санжаагийн Баярын Засгийн газар"]),
    ("Батболдын Засгийн газар", ["Сүхбаатарын Батболдын Засгийн газар"]),
    ("Алтанхуягийн Шинэчлэлийн Засгийн газар", ["Норовын Алтанхуягийн Засгийн газар"]),
    ("Сайханбилэгийн Засгийн газар", ["Чимэдийн Сайханбилэгийн Засгийн газар"]),
    ("Хүрэлсүхийн Засгийн газар", ["Ухнаагийн Хүрэлсүхийн Засгийн газар"]),
    ("Оюун-Эрдэнийн Засгийн газар", ["Лувсаннамсрайн Оюун-Эрдэнийн Засгийн газар"]),
]


def api_req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


def wiki_request(url, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fact-ledger"})) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                wait = 20 * (attempt + 1)
                print(f"    429 — {wait}s хүлээнэ…", flush=True)
                time.sleep(wait)
            else:
                raise
    return None


def wiki_exists(title):
    d = wiki_request("https://mn.wikipedia.org/w/api.php?action=query&titles="
                     + urllib.parse.quote(title) + "&format=json&redirects=1")
    if d is None:
        return False
    return not any("missing" in p for p in d["query"]["pages"].values())


def wiki_wikitext(title):
    d = wiki_request("https://mn.wikipedia.org/w/api.php?action=parse&page="
                     + urllib.parse.quote(title) + "&prop=wikitext&format=json&redirects=1")
    if d is None:
        return None
    return d["parse"]["wikitext"]["*"]


def clean(t):
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<font[^>]*>|</font>", "", t)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"'''?", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", t)
    return t.strip()


def parse_ministers(wt):
    """(нэр, албан тушаал) хосууд. Албан тушаал → Нэр дараалал нь элбэг."""
    wt = re.sub(r"<ref[^>]*/>", "", wt)
    wt = re.sub(r"<ref[^>]*>.*?</ref>", "", wt, flags=re.S)
    table_re = re.compile(r"\{\|(.*?)\n\|\}", re.S)
    row_re = re.compile(r"\n\|-\n?")
    out = []
    seen = set()

    def is_ministry(c):
        low = c.lower()
        return (("сайд" in low or low.endswith("дарга"))
                and "ерөнхийлөгч" not in low
                and "байнгын хороо" not in low
                and "Ерөнхий сайд" not in c
                and len(c) < 120)

    def is_person(c):
        low = c.lower()
        return (5 <= len(c) <= 55 and " " in c and not re.search(r"\d|[={]", c)
                and "сайд" not in low and "яам" not in low
                and "хороо" not in low and "засгийн" not in low
                and "тойрог" not in low and "хугацаа" not in low)

    for mtb in table_re.finditer(wt):
        tb = mtb.group(1)
        for row in row_re.split(tb):
            cells = []
            for line in row.split("\n"):
                if line.strip().startswith(("!", "{|", "|}")):
                    continue
                for part in line.split("||"):
                    part = part.strip()
                    if part.startswith("|"):
                        part = re.sub(r"^\|+\s*(?:rowspan\s*=\s*\d+\s*)?\|*", "", part).strip()
                    if not part:
                        continue
                    chosen = part
                    if "=" in chosen and "|" in chosen:
                        tail = chosen.rsplit("|", 1)[-1].strip().strip("[]").strip()
                        if tail:
                            chosen = tail
                    cells.append(clean(chosen))
            for i, c in enumerate(cells):
                if is_ministry(c):
                    for j in list(range(i + 1, min(len(cells), i + 4))) + list(range(i - 1, max(-1, i - 4), -1)):
                        if is_person(cells[j]):
                            key = (cells[j], c)
                            if key not in seen:
                                seen.add(key)
                                out.append((cells[j], c))
                            break
                    break
    return out


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    ents = {e["name"].lower(): e["id"] for e in api_req("GET", "/entities")}
    for a in api_req("GET", "/entities"):
        for al in a["aliases"]:
            ents.setdefault(al["alias"].lower(), a["id"])

    for cab_name, titles in CANDIDATES[start:]:
        gid = ents.get(cab_name.lower())
        if not gid:
            print("!! cabinet олдсонгүй:", cab_name, flush=True)
            continue
        got = None
        for t in titles:
            ex = wiki_exists(t)
            print(f"  probe: {t[:50]} -> {'EXISTS' if ex else 'missing'}", flush=True)
            if ex:
                got = t
                break
            time.sleep(2)
        if not got:
            print(f"MISSING: {cab_name}", flush=True)
            continue
        wt = wiki_wikitext(got)
        if not wt:
            print(f"FAILED to fetch: {got}", flush=True)
            continue
        ministers = parse_ministers(wt)
        print(f"== {cab_name}: {len(ministers)} сайд ==", flush=True)
        for n, ministry in ministers:
            eid = ents.get(n.lower())
            if eid:
                kind = "reuse"
            else:
                e = api_req("POST", "/entities", {
                    "name": n, "entity_type": "person",
                    "description": f"{ministry} ({cab_name})",
                })
                eid = e["id"]
                ents[n.lower()] = eid
                kind = "new"
            already = any(r["target_entity_id"] == gid
                          for r in api_req("GET", f"/entities/{eid}/relationships"))
            if already:
                kind += "/dupe-skip"
            else:
                api_req("POST", "/relationships", {
                    "source_entity_id": eid, "target_entity_id": gid,
                    "rel_type": f"сайд ({ministry})", "source_id": None,
                })
            print(f"  {n[:32]:32} | {ministry[:44]:44} [{kind}]", flush=True)
        time.sleep(3)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
