"""Agentic ingest туслах — API-аар дамжин нийтлэл татах/хадгалах.

Хэрэглээ:
  python agent_ingest.py scrape <url> <title>       # source үүсгэж блокуудыг хэвлэнэ
  python agent_ingest.py facts <entity_id> <spec.json>  # spec-д facts+rels бичсэн бол импортлоно
"""
import json
import sys
import urllib.request

API = "http://127.0.0.1:8020"


def req(method, path, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(API + path, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


def scrape_and_save(url, title):
    scraped = req("POST", "/scrape", {"url": url})
    blocks = [
        b for b in scraped["blocks"]
        if not b["text"].startswith("Ангилал:") and b["type"] in ("p", "h2", "h3", "li", "blockquote")
    ]
    if not blocks:
        raise SystemExit("NO_CONTENT")
    source = req("POST", "/sources", {
        "source_type": "article",
        "title": title,
        "url": url,
        "selected_blocks": [b["text"] for b in blocks],
        "raw_text": "\n\n".join(b["text"] for b in blocks),
    })
    print(f"SOURCE_ID={source['id']}")
    for b in blocks:
        print("---", b["type"], "|", b["text"])


def main():
    cmd = sys.argv[1]
    if cmd == "scrape":
        scrape_and_save(sys.argv[2], sys.argv[3])
    elif cmd == "facts":
        entity_id = sys.argv[2]
        spec = json.load(open(sys.argv[3], encoding="utf-8"))
        result = req("POST", f"/entities/{entity_id}/import-facts", spec)
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        raise SystemExit("unknown command")


if __name__ == "__main__":
    main()
