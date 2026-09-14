"""Нэр тулгах хэрэгслүүд: normalize, initials, fuzzy score.

alias_norm багана энэ normalize_name-ийн үр дүнг хадгална.
Анхаар: normalize_name-ийг өөрчилбөл entity_aliases.alias_norm-ийг
дахин тооцох data migration хэрэгтэй болно.
"""
import re

# Латин→кирилл ижил харагдах үсгүүд (холимог бичвэрээс хуулахад үүсдэг).
# Ө/Ү-г О/У руу нугалахгүй — эдгээр нь жинхэнэ ялгаа тул fuzzy зайд үлдээнэ.
_HOMOGLYPHS = str.maketrans({
    "a": "а", "b": "в", "c": "с", "e": "е", "h": "н", "k": "к",
    "m": "м", "o": "о", "p": "р", "t": "т", "x": "х", "y": "у",
})

_PUNCT_RE = re.compile(r"[.\-'\"«»""''‚,]+")
_WS_RE = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    """Нэрийг тулгахад бэлтгэнэ: casefold, homoglyph fold, цэг/зураас/хашилт
    арилгах, зайг нэг болгох."""
    if not name:
        return ""
    s = name.casefold()
    s = s.translate(_HOMOGLYPHS)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s
