"""Уян хатан огноо задлагч: нарийвчлал (precision) хадгална.

Дэмжих хэлбэрүүд:
  "1968"        → (1968-01-01, "year",  None)
  "1968-05"     → (1968-05-01, "month", None)
  "1968-05-15"  → (1968-05-15, "day",   None)
  "1968-1972"   → (1968-01-01, "range", 1972-01-01)
  None / хоосон → (None, None, None)
"""
import re
from datetime import date
from typing import Optional, Tuple

Precision = Optional[str]  # "day" | "month" | "year" | "range" | None


def parse_flexible_date(raw: Optional[str]) -> Tuple[Optional[date], Precision, Optional[date]]:
    if not raw:
        return None, None, None
    raw = str(raw).strip()

    m = re.match(r"^(\d{4})\s*[-–—]\s*(\d{4})$", raw)
    if m:
        start_y, end_y = int(m.group(1)), int(m.group(2))
        try:
            return date(start_y, 1, 1), "range", date(end_y, 1, 1)
        except ValueError:
            return None, None, None

    if re.match(r"^\d{4}$", raw):
        try:
            return date(int(raw), 1, 1), "year", None
        except ValueError:
            return None, None, None

    if re.match(r"^\d{4}-\d{2}$", raw):
        try:
            return date.fromisoformat(raw + "-01"), "month", None
        except ValueError:
            return None, None, None

    try:
        return date.fromisoformat(raw[:10]), "day", None
    except ValueError:
        return None, None, None


def format_flexible_date(d: Optional[date], precision: Precision, end: Optional[date] = None) -> Optional[str]:
    """Огноог нарийвчлалд нь тохируулан хэвлэнэ ("1996", "1996-05", "1996–1998")."""
    if d is None:
        return None
    if precision == "year":
        return str(d.year)
    if precision == "month":
        return f"{d.year}-{d.month:02d}"
    if precision == "range":
        return f"{d.year}–{end.year}" if end else str(d.year)
    return d.isoformat()
