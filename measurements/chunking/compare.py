"""Structure-aware chunking vs fixed windows. Run: `python main.py chunk-compare`.

Which documents are compared comes from `measurements/chunking/targets.yaml`.

Public API: `compare_chunkers(...)` -> Markdown table (also written to `output/chunk-compare.md`).

Columns: chunks, average and maximum tokens, chunks that start mid-sentence, table rows cut in
half, chunks with no section, and chunks over the 512-token limit of the embedding model.
"""

import re
from collections.abc import Callable
from pathlib import Path

import yaml

from src.rag.chunk import Counter, chunk_document
from src.rag.config import ChunkPaths, OUTPUT_DIR
from src.rag.store import read_markdown
from src.rag.tokens import count_tokens

from .fixed import fixed_chunks

TARGETS = Path(__file__).resolve().parent / "targets.yaml"
MODEL_LIMIT = 512
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_PAGE_MARKER = re.compile(r"^<!-- page (\d+) -->$", re.M)


def load_targets(path: Path = TARGETS) -> tuple[tuple[str, int | None], ...]:
    """(filename substring, last page or None) from the comparison config."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    docs = raw.get("documents")
    if not docs:
        raise ValueError(f"{path}: needs a documents list")
    targets = []
    for i, item in enumerate(docs, 1):
        match = item.get("match") if isinstance(item, dict) else None
        if not match:
            raise ValueError(f"{path}: document {i} needs match")
        pages = item.get("pages")
        if pages is not None and (not isinstance(pages, int) or pages < 1):
            raise ValueError(f"{path}: document {i} pages must be a positive integer")
        targets.append((str(match), pages))
    return tuple(targets)


def compare_chunkers(
    *,
    paths: ChunkPaths = ChunkPaths(),
    count: Counter = count_tokens,
    config: Path = TARGETS,
    targets: tuple[tuple[str, int | None], ...] | None = None,
    out: Path | None = OUTPUT_DIR / "chunk-compare.md",
    log: Callable[[str], None] = print,
) -> str:
    targets = load_targets(config) if targets is None else targets
    rows = []
    for needle, last_page in targets:
        matches = sorted(p for p in paths.md.glob("*.md") if needle in p.stem)
        if not matches:
            raise ValueError(f"no document in {paths.md} matches {needle!r}")
        front, body = read_markdown(matches[0])
        if last_page:
            body = _keep_pages(body, last_page)
        label = front["doc_id"].split("__", 1)[-1][:28] + (f" (p1-{last_page})" if last_page else "")
        log(f"compare: {label}")
        for name, chunks in (("by heading", chunk_document(front, body, count)),
                             ("fixed 400/80", fixed_chunks(front, body))):
            rows.append((label, name, _measure(chunks)))

    header = ("| Document | Strategy | Chunks | Avg tokens | Max tokens | Mid-sentence starts | Cut table rows "
              "| Empty section | Over 512 |\n|---|---|---|---|---|---|---|---|---|")
    lines = [
        f"| {label} | {name} | {m['chunks']} | {m['avg']} | {m['max']} | {m['mid_sentence']} "
        f"| {m['cut_rows']} | {m['empty_section']} | {m['over_limit']} |"
        for label, name, m in rows
    ]
    table = header + "\n" + "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(table, encoding="utf-8", newline="\n")
    return table


def _keep_pages(body: str, last_page: int) -> str:
    for marker in _PAGE_MARKER.finditer(body):
        if int(marker[1]) > last_page:
            return body[:marker.start()]
    return body


def _measure(chunks) -> dict:
    tokens = [c.n_tokens for c in chunks]
    return {
        "chunks": len(chunks),
        "avg": round(sum(tokens) / len(tokens)) if tokens else 0,
        "max": max(tokens, default=0),
        "mid_sentence": sum(_starts_mid_sentence(c.text) for c in chunks),
        "cut_rows": sum(_cut_rows(c.text) for c in chunks),
        "empty_section": sum(not c.section for c in chunks),
        "over_limit": sum(c.n_tokens > MODEL_LIMIT for c in chunks),
    }


def _starts_mid_sentence(text: str) -> bool:
    first = _COMMENT.sub("", text).lstrip()[:1]
    return first.isalpha() and first.islower()


def _cut_rows(text: str) -> int:
    """Table lines that have only one of the two outer pipes: a row that was cut."""
    lines = [line.strip() for line in text.split("\n")]
    return sum(1 for line in lines if line and (line.startswith("|") != line.endswith("|")))
