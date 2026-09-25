import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urlparse, unquote, quote

import httpx
from bs4 import BeautifulSoup
import trafilatura

REMOVE_TAGS = ["script", "style", "img", "video", "audio", "svg",
               "iframe", "noscript", "ins", "figure", "picture"]

REMOVE_CLASSES = ["ad", "ads", "advertisement", "banner", "promo",
                  "sidebar", "footer", "header", "nav", "menu",
                  "social", "share", "comment", "related"]

KEEP_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6",
             "p", "li", "blockquote", "strong", "em", "a"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "mn,en-US;q=0.9,en;q=0.8",
    # Accept-Encoding-г httpx-д үлдээнэ — бр(brotli) өргөтгөл суулгаагүй үед
    # гар аргаар тохируулбал задрахгүй хоцроно
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Wikipedia domain pattern
_WIKI_RE = re.compile(r"^(?:https?://)?([a-z]{2,})\.wikipedia\.org/wiki/(.+)$")


def _is_wikipedia(url: str) -> bool:
    return bool(_WIKI_RE.match(url))


_URLLIB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "mn,en-US;q=0.9,en;q=0.8",
}


def _wikitext_to_blocks(wikitext: str) -> list[dict]:
    """Strip wiki markup and return typed blocks {type, text}."""
    text = wikitext

    # Remove templates {{...}} — may be nested
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # Remove file/image links
    text = re.sub(r"\[\[(?:File|Image|Файл|Зураг):[^\]]*\]\]", "", text, flags=re.IGNORECASE)

    # Convert [[link|label]] → label, [[link]] → link
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)

    # Remove external links
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)

    # Remove <ref>...</ref>
    text = re.sub(r"<ref[^>]*/?>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/?>", "", text)

    # Remove HTML comments and tags
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    # Strip bold/italic markers
    text = re.sub(r"'{2,3}", "", text)

    # Parse line by line — detect headings vs body text
    blocks = []
    seen = set()
    for line in text.split("\n"):
        line = line.strip()

        # Detect wiki heading: == Heading ==
        heading_match = re.match(r"^(={2,6})\s*(.+?)\s*\1$", line)
        if heading_match:
            level = len(heading_match.group(1))  # 2=h2, 3=h3, etc.
            heading_text = heading_match.group(2).strip()
            if heading_text and heading_text not in seen:
                seen.add(heading_text)
                blocks.append({"type": f"h{level}", "text": heading_text})
            continue

        # Body text
        line = re.sub(r"\s+", " ", line)
        if len(line) < 15 or line in seen:
            continue
        seen.add(line)
        blocks.append({"type": "p", "text": line})

    return blocks


def _scrape_wikipedia(url: str) -> dict:
    """Use Wikipedia Special:Export (XML) — works where the API is rate-limited."""
    m = _WIKI_RE.match(url)
    lang = m.group(1)
    page_title = m.group(2)
    quoted_title = quote(unquote(page_title))
    export_url = f"https://{lang}.wikipedia.org/wiki/Special:Export/{quoted_title}"

    req = urllib.request.Request(export_url, headers=_URLLIB_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        xml_bytes = resp.read()

    # Parse MediaWiki XML export
    root = ET.fromstring(xml_bytes)
    ns = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}

    title_el = root.find(".//mw:title", ns)
    title = title_el.text if title_el is not None else unquote(page_title).replace("_", " ")

    text_el = root.find(".//mw:revision/mw:text", ns)
    if text_el is None or not text_el.text:
        raise ValueError("Wikipedia хуудаснаас контент олдсонгүй.")

    blocks = _wikitext_to_blocks(text_el.text)
    trafilatura_text = "\n\n".join([b["text"] for b in blocks])

    return {"title": title, "pub_date": None, "blocks": blocks, "trafilatura_text": trafilatura_text, "raw_html": xml_bytes.decode('utf-8', errors='ignore')}


def _extract_meta_date(soup: BeautifulSoup) -> Optional[str]:
    for prop in ["article:published_time", "article:modified_time", "og:updated_time"]:
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            return _parse_date_str(tag["content"])

    for name in ["pubdate", "date", "DC.date", "publishDate"]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return _parse_date_str(tag["content"])

    time_tag = soup.find("time", datetime=True)
    if time_tag:
        return _parse_date_str(time_tag["datetime"])

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            for key in ["datePublished", "dateCreated", "dateModified"]:
                if key in data:
                    return _parse_date_str(data[key])
        except Exception:
            pass

    return None


def _parse_date_str(raw: str) -> Optional[str]:
    raw = raw.strip()
    match = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if match:
        return match.group(1)
    return None


def _class_words(name: str) -> list[str]:
    """Split a CSS class name into lowercase words.

    Handles camelCase ("shareIcon" → ["share", "icon"]),
    hyphens ("post-share" → ["post", "share"]),
    and underscores ("post_share" → ["post", "share"]).
    """
    # Insert space before uppercase letters that follow lowercase (camelCase)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Replace hyphens and underscores with space
    name = re.sub(r"[-_]", " ", name)
    return [w for w in name.lower().split() if w]


_NOISE_SET = set(REMOVE_CLASSES)


def _is_noise_element(tag) -> bool:
    # Guard: decompose() sets attrs=None on recursively-decomposed children
    if not hasattr(tag, "attrs") or tag.attrs is None:
        return False
    classes = tag.get("class") or []
    tag_id = tag.get("id") or ""
    for name in list(classes) + [tag_id]:
        if any(word in _NOISE_SET for word in _class_words(name)):
            return True
    return False


def _scrape_html(url: str) -> dict:
    """Standard HTML scrape for non-Wikipedia URLs."""
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")
    pub_date = _extract_meta_date(soup)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else urlparse(url).netloc

    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        if _is_noise_element(tag):
            tag.decompose()

    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    BLOCK_TAGS   = {"div", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}
    INLINE_TAGS  = {"a", "strong", "em"}
    # div-г нэмж авна — зарим сайт <p> биш <div>-д текст тавьдаг
    EXTRACT_TAGS = KEEP_TAGS + ["div"]

    seen = set()
    blocks = []
    for el in soup.find_all(EXTRACT_TAGS):
        tag_name = el.name.lower()

        # Inline тагууд (a, strong, em): block-level эцэг тагтай бол алгасна
        # (эцэг тагаар аль хэдийн бүтэн текстийг нь барьсан байна)
        if tag_name in INLINE_TAGS:
            if el.find_parent(list(BLOCK_TAGS)):
                continue

        # <div>: зөвхөн шууд text агуулсан (хүүхэд div-гүй) блокийг авна
        if tag_name == "div":
            # Хүүхэд block-level тагтай div-г алгасна (давхардлаас зайлсхийх)
            if el.find(["div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]):
                continue

        text = el.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or text in seen:
            continue
        # Headings: include even if short; body text: min 15 chars
        if tag_name not in HEADING_TAGS and len(text) < 15:
            continue
        seen.add(text)
        blocks.append({"type": tag_name if tag_name != "div" else "p", "text": text})

    trafilatura_text = trafilatura.extract(html, include_links=True, include_formatting=True)

    return {
        "title": title, 
        "pub_date": pub_date, 
        "blocks": blocks, 
        "trafilatura_text": trafilatura_text, 
        "raw_html": html
    }


def scrape(url: str) -> dict:
    if _is_wikipedia(url):
        return _scrape_wikipedia(url)
    return _scrape_html(url)
