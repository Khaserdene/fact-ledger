"""AI-ийн гаралтын JSON-г засварлагч.

Гар (copy-paste) горимд AI markdown fence, экранлаагүй хашилт зэрэг
алдаа гаргадаг — эдгээрийг дарааллаар нь засаж json.loads оролдоно.
(frontend autoFixJson-ийн сервер талын порт + өргөтгөл)
"""
import json
import re
from typing import Any

# Текстэн утгатай талбарууд — мөр доторх экранлаагүй хашилтыг засна
_TEXT_FIELDS = [
    "fact", "source_quote", "reason", "new_fact_quote", "contradicted_fact_id",
    "role_context", "fact_id", "target_name", "rel_type", "target_kind",
    "name", "entity_type_guess", "quote", "name_a", "name_b", "topic", "stance",
]
_FIELD_RE = re.compile(
    r'^(\s*"(?:' + "|".join(_TEXT_FIELDS) + r')"\s*:\s*)"(.*)"(,?)\s*$'
)


def strip_markdown_fences(text: str) -> str:
    """```json ... ``` хүрээг арилгана."""
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text, re.DOTALL)
    if m:
        return m.group(1)
    return text


def extract_json_object(text: str) -> str:
    """Эхний { -ээс сүүлийн } хүртэлх хэсгийг ялгана (өмнө/хойно тайлбар текст байвал)."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text


def fix_inner_quotes(text: str) -> str:
    """Мөр бүрийн текстэн талбар доторх экранлаагүй хашилтыг \" болгоно."""
    out = []
    for line in text.split("\n"):
        m = _FIELD_RE.match(line)
        if not m:
            out.append(line)
            continue
        prefix, value, comma = m.groups()
        fixed = value.replace('\\"', "\x00").replace('"', '\\"').replace("\x00", '\\"')
        out.append(f'{prefix}"{fixed}"{comma}')
    return "\n".join(out)


def fix_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


def parse_json_lenient(raw: str) -> Any:
    """Дарааллаар засварлаж json.loads оролдоно. Бүтэлгүйтвэл ValueError."""
    candidates = []
    stage1 = strip_markdown_fences(raw)
    candidates.append(stage1)
    stage2 = extract_json_object(stage1)
    candidates.append(stage2)
    stage3 = fix_inner_quotes(stage2)
    candidates.append(stage3)
    stage4 = fix_trailing_commas(stage3)
    candidates.append(stage4)

    last_error = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (ValueError, TypeError) as e:
            last_error = e
    raise ValueError(f"JSON задлагдсангүй: {last_error}")
