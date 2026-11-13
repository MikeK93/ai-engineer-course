"""Clean-up of one document's chunks after they are cut. Public API: `clean_chunks(chunks, count, cap=...)`.

Order matters, and each step works on what the previous one left:
1. tag comparables: sale / rent comparables are kept but marked `skip_candidate` with a `skip_reason`
2. drop chunks that are only a page number, and chunks of one or two words that look like a title
3. drop exact duplicates inside the document (the first one stays)
4. squash tiny chunks into a neighbour (the previous one, else the next), keeping the squashed chunk's
   heading as a line of text so the label is not lost
5. number the survivors again, so `chunk_id` has no gaps

Returns the new chunks and a report of what each step did.
"""

import re
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from .config import CHUNK_MAX_TOKENS, CHUNK_TINY_TOKENS, COMPARABLES_PATTERN, MIN_WORDS_PER_CHUNK

if TYPE_CHECKING:
    from .chunk import Chunk

Counter = Callable[[str], int]

_COMPARABLES = re.compile(COMPARABLES_PATTERN, re.I)
_SALE = re.compile(r"\bsales?\b", re.I)
_RENT = re.compile(r"\b(?:rent|rental|lease|leases)\b", re.I)
# "6", "Page 6", "6 of 15", "Offering Memorandum | 5", "5 | Confidential": nothing but a page number
_PAGINATION = re.compile(
    r"^(?:[^|\d]{0,60}\|\s*)?(?:page\s*)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?(?:\s*\|\s*[^|\d]{0,60})?$", re.I)


def clean_chunks(chunks: list["Chunk"], count: Counter, *, cap: int = CHUNK_MAX_TOKENS,
                 tiny: int = CHUNK_TINY_TOKENS) -> tuple[list["Chunk"], dict]:
    report = {"skip_candidates": 0, "dropped_pagination": 0, "dropped_short": 0, "dropped_duplicate": 0, "squashed": 0}
    chunks = [_tag_comparables(c) for c in chunks]
    report["skip_candidates"] = sum(c.skip_candidate for c in chunks)

    kept = []
    for c in chunks:
        if is_pagination(c.text):
            report["dropped_pagination"] += 1
        elif is_too_short(c.text):
            report["dropped_short"] += 1
        else:
            kept.append(c)

    seen: set[str] = set()
    unique = []
    for c in kept:
        key = " ".join(c.text.lower().split())
        if key in seen:
            report["dropped_duplicate"] += 1
            continue
        seen.add(key)
        unique.append(c)

    squashed, report["squashed"] = _squash(unique, count, cap, tiny)
    numbered = [replace(c, chunk_id=f"{c.doc_id}#{i}") for i, c in enumerate(squashed)]
    return numbered, report


# --- steps ----------------------------------------------------------------------

def is_pagination(text: str) -> bool:
    lines = [re.sub(r"[*_`]+", "", line).strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    return bool(lines) and all(_PAGINATION.match(line) for line in lines)


def is_too_short(text: str) -> bool:
    """One or two words and no number: a title or a stray word, not something to retrieve."""
    return len(re.findall(r"\w+", text)) < MIN_WORDS_PER_CHUNK and not re.search(r"\d", text)


def _own_heading(chunk: "Chunk") -> str:
    return chunk.section.rsplit(" > ", 1)[-1] if chunk.section_source == "heading" else ""


def _tag_comparables(chunk: "Chunk") -> "Chunk":
    first_line = next((line for line in chunk.text.split("\n") if line.strip()), "")
    label = _own_heading(chunk)
    if not (_COMPARABLES.search(label) or (len(first_line) <= 100 and _COMPARABLES.search(first_line))):
        return chunk
    names = f"{label} {first_line}"
    reason = "sale comparables" if _SALE.search(names) else "rent comparables" if _RENT.search(names) else "comparables"
    return replace(chunk, skip_candidate=True, skip_reason=reason)


def _compatible(a: "Chunk", b: "Chunk") -> bool:
    return a.kind == b.kind and a.skip_candidate == b.skip_candidate and a.version_of == b.version_of


def _label_for(squashed: "Chunk", host: "Chunk") -> str:
    """The squashed chunk's own heading, as a text line, when it differs from the host's section."""
    label = _own_heading(squashed)
    if not label or squashed.section == host.section or squashed.text.lower().startswith(label.lower()):
        return ""
    return label + "\n"


def _merge(first: "Chunk", second: "Chunk", host: "Chunk", count: Counter) -> "Chunk":
    """`first` and `second` are neighbours; the result keeps `host`'s section and prefix."""
    other = second if host is first else first
    label = _label_for(other, host)
    if host is first:
        text = f"{first.text}\n\n{label}{second.text}"
    else:
        text = f"{label}{first.text}\n\n{second.text}"
    return replace(host, text=text, page_start=min(first.page_start, second.page_start),
                   page_end=max(first.page_end, second.page_end), ocr=first.ocr or second.ocr,
                   n_tokens=count(f"{host.embed_prefix}\n{text}"))


def _without_separators(text: str) -> str:
    """Table pipes, separator rows (`|---|---|`) and bold markers cost tokens but carry nothing, so the size of
    a chunk is judged on its words only: a table of empty cells is tiny however many `|` it has."""
    return re.sub(r"[|*_`:-]+", " ", text)


def _squash(chunks: list["Chunk"], count: Counter, cap: int, tiny: int) -> tuple[list["Chunk"], int]:
    chunks = list(chunks)
    merged = 0
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if count(_without_separators(c.text)) >= tiny:
            i += 1
            continue
        into_previous = chunks[i - 1] if i > 0 else None
        into_next = chunks[i + 1] if i + 1 < len(chunks) else None
        done = False
        for host, first, second, at in ((into_previous, into_previous, c, i - 1), (into_next, c, into_next, i)):
            if host is None or not _compatible(c, host):
                continue
            candidate = _merge(first, second, host, count)
            if candidate.n_tokens <= cap:
                chunks[at:at + 2] = [candidate]
                merged += 1
                i = max(at, 0)
                done = True
                break
        if not done:
            i += 1
    return chunks, merged
