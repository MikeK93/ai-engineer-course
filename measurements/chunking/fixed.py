"""Baseline for the comparison only: fixed token windows that ignore headings, tables and sentences.

Not used by the pipeline. `compare.py` measures it against `src.rag.chunk`.
"""

import re
from collections.abc import Callable

from src.rag.chunk import Chunk
from src.rag.tokens import token_spans

WINDOW_TOKENS = 400
OVERLAP_TOKENS = 80
_PAGE_MARKER = re.compile(r"<!-- page (\d+) -->")


def fixed_chunks(
    front: dict,
    body: str,
    *,
    size: int = WINDOW_TOKENS,
    overlap: int = OVERLAP_TOKENS,
    spans_of: Callable[[str], list[tuple[int, int]]] = token_spans,
) -> list[Chunk]:
    """Cut `body` (page markers included, as a naive pipeline would see it) every `size - overlap` tokens."""
    spans = spans_of(body)
    markers = [(m.start(), int(m[1])) for m in _PAGE_MARKER.finditer(body)]
    first_page = int(str(front.get("pages", "1")).split("-")[0])

    def page_at(offset: int) -> int:
        page = first_page
        for position, number in markers:
            if position > offset:
                break
            page = number
        return page

    chunks: list[Chunk] = []
    step = size - overlap
    for start in range(0, len(spans), step):
        window = spans[start:start + size]
        first, last = window[0][0], window[-1][1]
        chunks.append(Chunk(
            chunk_id=f"{front['doc_id']}#{len(chunks)}", doc_id=front["doc_id"], source=front["source"],
            title=front["title"], section="", section_source="none", embed_prefix="",
            doc_type=front["doc_type"], as_of=str(front["as_of"]), version_of=front.get("version_of"),
            replaces=front.get("replaces"), doc_hash=front["content_hash"], page_start=page_at(first),
            page_end=page_at(last), kind="content", ocr=False, n_tokens=len(window), text=body[first:last],
        ))
        if start + size >= len(spans):
            break
    return chunks
