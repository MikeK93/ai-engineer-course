"""Split a file into logical documents when it contains an addendum, and suggest where.

`split_versions` follows the catalog (`versions:` in doc_meta.yaml); `find_version_markers`
only *suggests* split points so a human adds them to the catalog. Nothing is split silently.
"""

import re
from dataclasses import replace

from .meta import DocEntry
from .models import LogicalDoc, Page

_MARKER = re.compile(r"^[#*\s]*(addendum|supplement|amendment|errata|amended and restated)\b.{0,60}$", re.I)
MAX_MARKER_LINE = 70


def split_versions(entry: DocEntry, pages: list[Page]) -> list[LogicalDoc]:
    """One LogicalDoc for a plain file; one per `versions:` item otherwise."""
    common = dict(source=entry.file, doc_type=entry.doc_type, source_url=entry.source_url)
    if not entry.versions:
        return [LogicalDoc(doc_id=entry.doc_id, title=entry.title, as_of=entry.as_of, pages=pages, **common)]

    starts = [_resolve_start(v.start, pages, entry.file) for v in entry.versions]
    if starts[0] != 1 or starts != sorted(set(starts)):
        raise ValueError(f"{entry.file}: version starts must begin at page 1 and increase, got {starts}")

    ends = [s - 1 for s in starts[1:]] + [len(pages)]
    return [
        LogicalDoc(
            doc_id=f"{entry.doc_id}@{v.suffix}", title=f"{entry.title} ({v.suffix})", as_of=v.as_of,
            pages=pages[begin - 1:end], version_of=entry.doc_id, replaces=v.replaces, **common,
        )
        for v, begin, end in zip(entry.versions, starts, ends)
    ]


def _resolve_start(start: int | str, pages: list[Page], file: str) -> int:
    if isinstance(start, int):
        if not 1 <= start <= len(pages):
            raise ValueError(f"{file}: version start page {start} is outside 1..{len(pages)}")
        return start
    wanted = start.strip().lower()
    for page in pages:
        if any(line.strip(" #*").lower().startswith(wanted) for line in page.text.splitlines()):
            return page.number
    raise ValueError(f"{file}: version start heading {start!r} not found")


def find_version_markers(pages: list[Page]) -> list[tuple[int, str]]:
    """(page number, heading line) for pages that look like the start of an addendum."""
    found = []
    for page in pages:
        for line in page.text.splitlines():
            if len(line.strip()) <= MAX_MARKER_LINE and _MARKER.match(line.strip()):
                found.append((page.number, line.strip()))
                break
    return found
