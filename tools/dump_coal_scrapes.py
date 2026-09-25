# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.abspath('backend'))
sys.stdout.reconfigure(encoding='utf-8')
import scraper

os.makedirs('tools/coal_scrapes', exist_ok=True)
urls = {
    'ikon_2qpk': 'https://ikon.mn/n/2qpk',
    'ikon_3169': 'https://ikon.mn/n/3169',
    'zarig_12fc': 'https://zarig.mn/12fc',
    'zarig_12fe': 'https://zarig.mn/12fe',
    'zarig_12nl': 'https://zarig.mn/12nl',
    'zarig_12tm': 'https://zarig.mn/12tm',
    'zarig_18ib': 'https://zarig.mn/18ib',
    'news_2774450': 'https://news.mn/r/2774450/',
    'wiki_coal': 'https://mn.wikipedia.org/wiki/Нүүрсний_хулгайн_хэрэг',
    'mpress_1004931': 'https://mpress.mn/p/1004931',
    'ikon_2qfn': 'https://ikon.mn/n/2qfn',
    'news_2694237': 'https://news.mn/r/2694237/',
    'ergelt_55076': 'https://ergelt.mn/news/22/single/55076'
}

for key, u in urls.items():
    try:
        res = scraper.scrape(u)
        blocks = [b['text'].strip() for b in res.get('blocks', []) if len(b['text'].strip()) > 5]
        with open(f'tools/coal_scrapes/{key}.txt', 'w', encoding='utf-8') as f:
            f.write(f"URL: {u}\nTITLE: {res.get('title', '')}\nPUB_DATE: {res.get('pub_date', '')}\n\n")
            f.write('\n\n'.join(blocks))
        print(f"Done: {key} ({len(blocks)} blocks)")
    except Exception as e:
        print(f"Error {key}: {e}")
