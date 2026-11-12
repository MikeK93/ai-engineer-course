"""Clean extracted pages so the same text always looks the same.

Public API: `normalize_pages(pages)`. It is a pure function over the whole document because
two of the fixes (repeated headers/footers) can only be seen by comparing pages.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import replace

from .models import OK, Page

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_BR = re.compile(r"<br\s*/?>", re.I)
_INLINE_TAG = re.compile(r"</?(?:u|b|i|em|strong|sup|sub|span)\b[^>]*>", re.I)
_LEADERS = re.compile(r"(?:\s?\.){4,}")        # table-of-contents dot leaders: "Fees ........ 14", "Fees . . . . 14"
_TABLE_SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")   # |-----|:---:|  (padded wide by some converters)
_SEPARATOR_DASHES = re.compile(r"-{4,}")             # every dash is a token for the embedding model
_PAGE_OF = re.compile(r"^\|?\s*(?:page\s+)?\d{1,4}\s*(?:of|/)\s*\d{1,4}\s*\|?$", re.I)
_BARE_NUMBER = re.compile(r"^\|?\s*(?:page\s+)?\d{1,4}\s*\|?$", re.I)
_HYPHEN_BREAK = re.compile(r"(?<=[a-z])-\n(?=[a-z])")
_EXTRA_SPACE = re.compile(r"(?<=\S)[ \t]{2,}")
_DIGITS = re.compile(r"\d+")

REPEAT_SHARE = 0.4        # a line on >= 40% of pages is a running header or footer
MIN_PAGES_FOR_REPEATS = 5
EDGE_LINES = 3            # only the first/last lines of a page can be headers/footers


def normalize_pages(pages: list[Page]) -> list[Page]:
    cleaned = [replace(p, text=_clean_text(p.text)) if p.status == OK else p for p in pages]
    repeated = _repeated_edge_lines([p.text for p in cleaned if p.status == OK])
    out = []
    for p in cleaned:
        if p.status != OK:
            out.append(p)
            continue
        text = _drop_page_furniture(p.text, repeated)
        out.append(replace(p, text=text))
    return out


def _clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf" and (c in "\n\t" or c >= " "))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _COMMENT.sub("", text)
    text = _BR.sub(" ", text)
    text = _INLINE_TAG.sub("", text)
    text = _LEADERS.sub(" ", text)               # each dot is a token for the embedding model: pure noise
    lines = [_EXTRA_SPACE.sub(" ", line).rstrip() for line in text.split("\n")]
    lines = [_SEPARATOR_DASHES.sub("---", line) if _TABLE_SEPARATOR.match(line) else line for line in lines]
    text = "\n".join(lines)
    text = _HYPHEN_BREAK.sub("", text)
    return text.strip()


def _edge_lines(lines: list[str]) -> list[int]:
    """Indexes of non-empty lines within EDGE_LINES of the top or bottom of the page."""
    filled = [i for i, line in enumerate(lines) if line.strip()]
    return sorted(set(filled[:EDGE_LINES] + filled[-EDGE_LINES:]))


def _shape(line: str) -> str:
    """A line with digits masked, so 'Confidential - 12' and 'Confidential - 13' compare equal."""
    return _DIGITS.sub("#", line.strip().lower())


def _repeated_edge_lines(texts: list[str]) -> set[str]:
    if len(texts) < MIN_PAGES_FOR_REPEATS:
        return set()
    seen: Counter[str] = Counter()
    for text in texts:
        lines = text.split("\n")
        seen.update({_shape(lines[i]) for i in _edge_lines(lines)})
    limit = REPEAT_SHARE * len(texts)
    # Table rows ("|") are never treated as furniture: a repeated column header is still content.
    return {s for s, n in seen.items() if n >= limit and len(s) > 3 and s != "#" and not s.startswith("|")}


def _drop_page_furniture(text: str, repeated: set[str]) -> str:
    lines = text.split("\n")
    edge = set(_edge_lines(lines))
    keep = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and _PAGE_OF.match(stripped):
            continue
        if i in edge and stripped and (_BARE_NUMBER.match(stripped) or _shape(stripped) in repeated):
            continue
        keep.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip()
