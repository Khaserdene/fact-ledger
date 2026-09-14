import difflib
from sqlalchemy.orm import Session
import models
import scraper
from hasher import stable_hash

def verify_article(db: Session, article: models.Source) -> dict:
    """
    Verifies if the saved article's selected text is still present in the live article.
    If it's unchanged, returns unchanged=True.
    If changed, computes an HTML diff of the cleaned text.
    """
    # 1. Scrape live URL
    scrape_result = scraper.scrape(article.url)
    
    # We prefer trafilatura_text if available, otherwise fallback to blocks
    live_raw = scrape_result.get("trafilatura_text")
    if not live_raw:
        live_raw = "\n\n".join([b["text"] for b in scrape_result.get("blocks", [])])

    live_raw_hash = stable_hash(live_raw)

    # 2. Check if selected_text is perfectly inside live_raw (substring match)
    # Because selected_text might have been modified slightly or whitespace issues,
    # we can do a direct substring check.
    # To be safer with whitespaces, we could remove extra whitespaces from both.
    
    def normalize(text):
        return " ".join(text.split())

    norm_selected = normalize(article.selected_text)
    norm_live = normalize(live_raw)

    if norm_selected in norm_live:
        return {
            "unchanged": True,
            "live_raw_hash": live_raw_hash,
            "message": "Өөрчлөгдөөгүй. Таны сонгосон баримт эх сурвалж дээр яг хэвээрээ байна.",
            "diff_html": None
        }

    # 3. If changed, we generate a Git-like Diff between the OLD cleaned_text and NEW live_raw
    # We use difflib to show what changed
    differ = difflib.HtmlDiff()
    # difflib wants a list of lines
    old_lines = article.cleaned_text.splitlines()
    new_lines = live_raw.splitlines()
    
    diff_html = differ.make_table(old_lines, new_lines, fromdesc="Анхны хадгалсан хувилбар", todesc="Одоогийн амьд хувилбар", context=True, numlines=3)
    
    return {
        "unchanged": False,
        "live_raw_hash": live_raw_hash,
        "message": "Анхаар! Нийтлэлийн агуулга өөрчлөгдсөн эсвэл устгагдсан байна.",
        "diff_html": diff_html
    }
