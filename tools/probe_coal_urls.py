# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.abspath("backend"))
sys.stdout.reconfigure(encoding="utf-8")
import scraper

urls = [
    "https://ikon.mn/n/2qpk",
    "https://ikon.mn/n/3169",
    "https://zarig.mn/12fc",
    "https://zarig.mn/12fe",
    "https://zarig.mn/12nl",
    "https://zarig.mn/12tm",
    "https://zarig.mn/18ib",
    "https://news.mn/r/2774450/",
    "https://mn.wikipedia.org/wiki/Нүүрсний_хулгайн_хэрэг",
    "https://mpress.mn/p/1004931"
]

for u in urls:
    res = scraper.scrape(u)
    title = res.get("title", "")
    blocks = [b["text"].strip() for b in res.get("blocks", []) if len(b["text"].strip()) > 10]
    print(f"URL: {u}\nTitle: {title}\nBlocks: {len(blocks)}\nFirst 3 blocks:")
    for b in blocks[:3]:
        print(f"  - {b[:120]}...")
    print("="*60)
