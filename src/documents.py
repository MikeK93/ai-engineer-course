import base64
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import tiktoken

from .config import PDFS, TEXTS

_enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class Document:
    source_file: str
    text: str | None = None
    pdf_b64: str | None = None
    pages_total: int = 0
    pages_used: int = 0
    tokens_used: int = 0


def extract_text(pdf_path: Path) -> list[str]:
    """Raw per-page text, cached in data/texts/ as pages separated by form feeds."""
    cache = TEXTS / (pdf_path.stem + ".txt")
    if cache.exists():
        return cache.read_text(encoding="utf-8").split("\f")
    with pymupdf.open(pdf_path) as doc:
        pages = [page.get_text() for page in doc]
    TEXTS.mkdir(parents=True, exist_ok=True)
    cache.write_text("\f".join(pages), encoding="utf-8")
    return pages


def load_document(source_file: str, mode: str, max_pages: int, max_tokens: int) -> Document:
    pdf_path = PDFS / source_file
    if mode == "pdf":
        with pymupdf.open(pdf_path) as src:
            total = len(src)
            if total > max_pages:
                src.select(range(max_pages))
            data = src.tobytes()
        return Document(
            source_file,
            pdf_b64=base64.b64encode(data).decode(),
            pages_total=total,
            pages_used=min(total, max_pages),
        )

    pages = extract_text(pdf_path)
    text = "\n\n".join(pages[:max_pages])
    tokens = _enc.encode(text, disallowed_special=())
    if len(tokens) > max_tokens:
        text = _enc.decode(tokens[:max_tokens])
        tokens = tokens[:max_tokens]
    return Document(
        source_file,
        text=text,
        pages_total=len(pages),
        pages_used=min(len(pages), max_pages),
        tokens_used=len(tokens),
    )


def list_sources() -> list[str]:
    return sorted(p.name for p in PDFS.glob("*.pdf"))
