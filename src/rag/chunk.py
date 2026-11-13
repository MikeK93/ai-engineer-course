"""Markdown documents -> chunks that keep the document's structure.

Public API:
- `chunk_document(front, body, count=...)`: one document -> list[Chunk]
- `chunk_corpus(...)`: every file in `data/md/` -> `data/chunks.jsonl` + `data/chunks_manifest.json`.
  When that manifest changes, the previous one is moved to
  `data/manifests/chunks-manifest-<pipeline_version>-<hash>.json` (never overwritten).

How a document is cut:
1. The body is parsed into blocks: heading, paragraph, list, table (page markers set the page).
2. Headings form a path (`Offering Summary > Pricing`). That path is the chunk's `section`.
3. Whole blocks are packed into a chunk up to the target size. A new heading starts a new chunk
   only when the current one already has CHUNK_MIN_TOKENS, so tiny sections are not left alone.
4. A block bigger than the hard cap is split: a table between rows (header row repeated), a list
   between items, a paragraph between sentences. This is the only way a paragraph is ever cut.
5. Sizes are measured on what gets embedded: `embed_prefix` (title + section) plus the text.
6. A sentence is never cut while it fits the embedding model (512 tokens with the prefix). Headings that carry
   a figure (`ASKING PRICE: $1,189,900`) stay in the text, and a sentence split by a page break is rejoined.
7. `chunk_clean` then drops pagination-only, title-like and duplicate chunks, squashes tiny ones into a
   neighbour and tags sale / rent comparables as `skip_candidate`.

The token counter is injected, so tests run without downloading a model.
"""

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from .chunk_clean import clean_chunks
from .config import (BOILERPLATE_HEADINGS, BOILERPLATE_PHRASES, CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS,
                     CHUNK_MODEL_MAX_TOKENS, CHUNK_TINY_TOKENS, CHUNK_TOKENS, EMBED_MODEL, PIPELINE_VERSION,
                     ChunkPaths)
from .store import archive_manifest_if_changed, read_json, read_markdown, write_json
from .tokens import count_tokens

Counter = Callable[[str], int]
MAX_PREFIX_TOKENS = 100           # title + section path may use at most this much of the cap

_PAGE = re.compile(r"^<!-- page (\d+) -->$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_LIST = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+")
_SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")          # a pipe that is not escaped as \|
# A sentence ends at . ! ? (optionally followed by a closing quote or bracket) and the next one starts with a capital.
_SENTENCE_END = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"\u201d\u2019')\]]))\s+(?=[A-Z0-9$\"\u201c'(\[])")
_SENTENCE_FINAL = re.compile(r"[.!?:;][\"\u201d\u2019')\]*_]*$")
_CLAUSE_END = re.compile(r"(?<=[;:])\s+")
# A figure in a heading: a dollar amount, a number with thousands separators, or a size (`2.0 FAR`, `5 acres`, `7%`).
_FIGURE = re.compile(r"\$|\d{1,3}(?:,\d{3})+|\b\d+(?:\.\d+)?\s?(?:sf|sq\.? ?ft|far|acres?|units?|%)", re.I)
SENTENCE_SLACK = CHUNK_MODEL_MAX_TOKENS - CHUNK_MAX_TOKENS   # a sentence may use the room between the cap and the model limit


@dataclass(frozen=True)
class Chunk:
    chunk_id: str             # "<doc_id>#<index>", stable while the document is unchanged
    doc_id: str
    source: str
    title: str
    section: str              # heading path, or "<title> > page <n>" when the document has no heading there
    section_source: str       # "heading", "page", or "none" (fixed-window baseline)
    embed_prefix: str         # what is put before the text when embedding: title + heading path (or title)
    doc_type: str
    as_of: str
    version_of: str | None
    replaces: str | None
    doc_hash: str             # content_hash of the document in data/md/
    page_start: int
    page_end: int
    kind: str                 # "content" or "boilerplate" (kept, but excluded from search)
    ocr: bool                 # any page in the chunk came from OCR
    n_tokens: int             # embed_prefix + text, in embedding-model tokens
    text: str
    pipeline_version: str = PIPELINE_VERSION
    skip_candidate: bool = False     # sale / rent comparables: kept, but a candidate to leave out of search
    skip_reason: str | None = None


@dataclass
class _Block:
    kind: str                 # heading | paragraph | list | table
    text: str
    page: int
    level: int = 0


@dataclass
class _Context:
    section: str
    section_source: str
    prefix: str
    prefix_tokens: int
    stack: tuple = ()          # the heading stack when the chunk started


# --- parsing --------------------------------------------------------------------

def _first_page(front: dict) -> int:
    return int(str(front.get("pages", "1")).split("-")[0])


def _is_boilerplate_heading(name: str) -> bool:
    return any(word in name.lower() for word in BOILERPLATE_HEADINGS)


def _clean_heading(text: str) -> str:
    return " ".join(re.sub(r"[*_`]+", "", text).split())


def _parse_blocks(body: str, first_page: int) -> list[_Block]:
    blocks: list[_Block] = []
    lines: list[str] = []
    kind = ""
    page = start_page = first_page

    def flush() -> None:
        nonlocal lines
        if lines:
            blocks.append(_Block(kind, "\n".join(lines).strip(), start_page))
            lines = []

    for raw in body.splitlines():
        line = raw.rstrip()
        marker = _PAGE.match(line.strip())
        if marker:
            flush()
            page = int(marker[1])
            continue
        if not line.strip():
            flush()
            continue
        heading = _HEADING.match(line)
        if heading:
            flush()
            text = _clean_heading(heading[2])
            if text:
                blocks.append(_Block("heading", text, page, len(heading[1])))
            continue
        this = "table" if line.startswith("|") else "list" if _LIST.match(line) else "paragraph"
        if lines and this != kind and not (kind == "list" and line[:1] == " "):
            flush()
        if not lines:
            kind, start_page = this, page
        lines.append(line)
    flush()
    return _attach_titles(_join_split_paragraphs(_keep_numeric_headings(blocks)))


def _keep_numeric_headings(blocks: list[_Block]) -> list[_Block]:
    """A heading is normally only a label (`section`), but some carry the fact itself: `ASKING PRICE: $1,189,900`,
    `$10,000,000`, `37,312 SF`. A heading with such a figure and no text of its own stays in the text, and a
    heading with a dollar amount is repeated in the text, so the figure can be found and quoted.
    Headings like `ITEM 2` or `2.1 Structure` have numbers too, but they are only labels."""
    out: list[_Block] = []
    for i, block in enumerate(blocks):
        if block.kind != "heading" or not _FIGURE.search(block.text):
            out.append(block)
            continue
        following = blocks[i + 1] if i + 1 < len(blocks) else None
        bare = following is None or (following.kind == "heading" and following.level <= block.level)
        if bare:
            out.append(_Block("paragraph", block.text, block.page))
        else:
            out.append(block)
            if "$" in block.text:
                out.append(_Block("paragraph", block.text, block.page))
    return out


def _join_split_paragraphs(blocks: list[_Block]) -> list[_Block]:
    """Rejoin a sentence the page layout cut in two: a paragraph that does not end a sentence, followed by a
    paragraph that starts in lower case, is one paragraph (page break, column break)."""
    out: list[_Block] = []
    for block in blocks:
        if (out and out[-1].kind == "paragraph" and block.kind == "paragraph" and block.text[:1].islower()
                and not _SENTENCE_FINAL.search(out[-1].text)):
            out[-1] = _Block("paragraph", f"{out[-1].text} {block.text}", out[-1].page)
        else:
            out.append(block)
    return out


def _looks_like_title(block: _Block) -> bool:
    """A short single line the converter did not mark as a heading, for example `INVESTMENT OVERVIEW`."""
    text = block.text
    return (block.kind == "paragraph" and "\n" not in text and len(text.split()) <= 10 and len(text) <= 80
            and text[:1].isupper() and text[-1] not in ".,;!?")


def _attach_titles(blocks: list[_Block]) -> list[_Block]:
    """Keep a title-like line with the paragraph or list that follows it, so it is never left at a chunk's end."""
    out: list[_Block] = []
    for block in blocks:
        if out and _looks_like_title(out[-1]) and block.kind in ("paragraph", "list"):
            title = out.pop()
            block = _Block(block.kind, f"{title.text}\n{block.text}", title.page)
        out.append(block)
    return out


# --- splitting an oversized block ------------------------------------------------

def _join_units(units: list[str], sep: str, limit: int, count: Counter) -> list[str]:
    out: list[str] = []
    current: list[str] = []
    used = 0
    for unit in units:
        n = count(unit)
        if current and used + n > limit:
            out.append(sep.join(current))
            current, used = [], 0
        current.append(unit)
        used += n
    if current:
        out.append(sep.join(current))
    return out


def _split_text(text: str, limit: int, count: Counter, slack: int = SENTENCE_SLACK) -> list[str]:
    """Cut between sentences. A sentence is never cut while it fits the embedding model (limit + slack); only
    a longer one is cut, at `;` or `:` first and between words as a last resort."""
    units: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        if count(sentence) <= limit + slack:
            units.append(sentence)
            continue
        for clause in _CLAUSE_END.split(sentence):
            units.extend([clause] if count(clause) <= limit else _join_units(clause.split(), " ", limit, count))
    return _join_units(units, " ", limit, count)


def _split_wide_row(row: str, limit: int, count: Counter) -> list[str]:
    """A row too big for one chunk becomes several complete rows: its longest cell is cut between
    sentences and the other cells (the labels) are repeated in each new row. Rows are never cut mid-row."""
    if count(row) <= limit:
        return [row]
    cells = [c.strip() for c in _CELL_SPLIT.split(row.strip().strip("|"))]
    widest = max(range(len(cells)), key=lambda i: len(cells[i]))
    others = [c for i, c in enumerate(cells) if i != widest]
    room = limit - count(" | ".join(others)) - len(cells) - 2
    if room < 20:
        return [row]                                   # the labels alone fill the chunk: leave the row whole
    rows = []
    for part in _split_text(cells[widest], room, count, slack=0):
        new = cells[:widest] + [part] + cells[widest + 1:]
        rows.append("|" + "|".join(new) + "|")
    return rows


def _split_table(text: str, limit: int, count: Counter) -> list[str]:
    lines = text.split("\n")
    header = lines[:2] if len(lines) > 1 and _SEPARATOR.match(lines[1].strip()) else []
    head_tokens = count("\n".join(header)) if header else 0
    pieces: list[str] = []
    rows: list[str] = []
    used = head_tokens
    body_rows = [r for row in lines[len(header):] for r in _split_wide_row(row, limit - head_tokens, count)]
    for row in body_rows:
        n = count(row)
        if rows and used + n > limit:
            pieces.append("\n".join(header + rows))
            rows, used = [], head_tokens
        rows.append(row)
        used += n
    if rows:
        pieces.append("\n".join(header + rows))
    return pieces


def _split_block(block: _Block, limit: int, count: Counter) -> list[str]:
    if count(block.text) <= limit:
        return [block.text]
    if block.kind == "table":
        return _split_table(block.text, limit, count)
    if block.kind == "list":
        items: list[str] = []
        for line in block.text.split("\n"):
            if items and not _LIST.match(line):
                items[-1] += "\n" + line           # continuation line of the previous item
            else:
                items.append(line)
        pieces: list[str] = []
        for item in items:
            pieces.extend([item] if count(item) <= limit else _split_text(item, limit, count))
        return _join_units(pieces, "\n", limit, count)
    return _split_text(block.text, limit, count)


# --- one document ----------------------------------------------------------------

def chunk_document(front: dict, body: str, count: Counter = count_tokens, **sizes) -> list[Chunk]:
    """One document -> cut by heading, then cleaned (see `chunk_clean`). `sizes`: target, cap, min_tokens."""
    return chunk_document_with_report(front, body, count, **sizes)[0]


def chunk_document_with_report(
    front: dict,
    body: str,
    count: Counter = count_tokens,
    *,
    target: int = CHUNK_TOKENS,
    cap: int = CHUNK_MAX_TOKENS,
    min_tokens: int = CHUNK_MIN_TOKENS,
    tiny: int = CHUNK_TINY_TOKENS,
) -> tuple[list[Chunk], dict]:
    cut = _cut(front, body, count, target, cap, min_tokens)
    return clean_chunks(cut, count, cap=cap, tiny=tiny)


def _cut(front: dict, body: str, count: Counter, target: int, cap: int, min_tokens: int) -> list[Chunk]:
    title = front["title"]
    ocr_pages = set(front.get("ocr_pages", []))
    prefix_memo: dict[str, int] = {}

    def prefix_tokens(prefix: str) -> int:
        if prefix not in prefix_memo:
            prefix_memo[prefix] = count(prefix)
        return prefix_memo[prefix]

    stack: list[tuple[int, str]] = []
    chunks: list[Chunk] = []
    parts: list[str] = []
    pages: set[int] = set()
    used = 0
    ctx: _Context | None = None

    def context(page: int) -> _Context:
        names = [name for _, name in stack]
        if not names:
            return _Context(f"{title} > page {page}", "page", title, prefix_tokens(title))
        snapshot = tuple(stack)
        while len(names) > 1 and prefix_tokens(f"{title} | {' > '.join(names)}") > MAX_PREFIX_TOKENS:
            names = names[1:]                      # drop the outermost heading first
        prefix = f"{title} | {' > '.join(names)}"
        while prefix_tokens(prefix) > MAX_PREFIX_TOKENS and " " in prefix:
            prefix = prefix.rsplit(" ", 1)[0]      # last resort: shorten by words
        return _Context(" > ".join(name for _, name in stack), "heading", prefix, prefix_tokens(prefix), snapshot)

    def flush() -> None:
        nonlocal parts, pages, used, ctx
        if not parts:
            return
        text = "\n\n".join(parts)
        lowered = text.lower()
        own_heading = ctx.section.rsplit(" > ", 1)[-1]        # the innermost heading, not its parents
        boilerplate = _is_boilerplate_heading(own_heading) or any(lowered.startswith(p) for p in BOILERPLATE_PHRASES)
        chunks.append(Chunk(
            chunk_id=f"{front['doc_id']}#{len(chunks)}", doc_id=front["doc_id"], source=front["source"],
            title=title, section=ctx.section, section_source=ctx.section_source, embed_prefix=ctx.prefix,
            doc_type=front["doc_type"], as_of=str(front["as_of"]), version_of=front.get("version_of"),
            replaces=front.get("replaces"), doc_hash=front["content_hash"], page_start=min(pages),
            page_end=max(pages), kind="boilerplate" if boilerplate else "content",
            ocr=bool(pages & ocr_pages), n_tokens=count(f"{ctx.prefix}\n{text}"), text=text,
        ))
        parts, pages, used, ctx = [], set(), 0, None

    for block in _parse_blocks(body, _first_page(front)):
        if block.kind == "heading":
            # The converter's heading levels are unreliable: later sections often come out as children of
            # "Table of contents" or "Disclaimer". Those headings never contain subsections.
            stack[:] = [(level, name) for level, name in stack if not _is_boilerplate_heading(name)]
            while stack and stack[-1][0] >= block.level:
                stack.pop()
            stack.append((block.level, block.text))
            if parts:
                # A small chunk keeps its own child subsection; any other heading starts a new chunk.
                is_child = bool(ctx.stack) and len(stack) > len(ctx.stack) and tuple(stack[:len(ctx.stack)]) == ctx.stack
                clean = not _is_boilerplate_heading(block.text) and not _is_boilerplate_heading(ctx.stack[-1][1]) if ctx.stack else False
                if is_child and clean and used < min_tokens:
                    parts.append(block.text)
                    pages.add(block.page)
                    used += count(block.text)
                else:
                    flush()
            continue

        new_ctx = context(block.page)
        reserved = max(new_ctx.prefix_tokens, ctx.prefix_tokens if ctx else 0)
        for piece in _split_block(block, cap - reserved, count):
            n = count(piece)
            if parts and used + n > min(target, cap - ctx.prefix_tokens):
                flush()
            if not parts:
                ctx = context(block.page)
            parts.append(piece)
            pages.add(block.page)
            used += n
    flush()
    return chunks


# --- the whole corpus --------------------------------------------------------------

def chunk_corpus(
    *,
    paths: ChunkPaths = ChunkPaths(),
    count: Counter = count_tokens,
    only: list[str] | None = None,
    log: Callable[[str], None] = print,
) -> dict:
    """Chunk every Markdown file, write `chunks.jsonl` and a summary, return the summary."""
    files = sorted(p for p in paths.md.glob("*.md") if not only or any(t in p.stem for t in only))
    if not files:
        raise ValueError(f"no Markdown files to chunk in {paths.md}" + (f" matching {only}" if only else ""))

    all_chunks: list[Chunk] = []
    per_doc: dict[str, dict] = {}
    totals: dict[str, int] = {}
    for path in files:
        front, body = read_markdown(path)
        chunks, report = chunk_document_with_report(front, body, count)
        all_chunks.extend(chunks)
        per_doc[front["doc_id"]] = {
            "chunks": len(chunks),
            "boilerplate": sum(c.kind == "boilerplate" for c in chunks),
            "page_sections": sum(c.section_source == "page" for c in chunks),
            **report,
        }
        for key, n in report.items():
            totals[key] = totals.get(key, 0) + n
    log(f"chunk: {len(all_chunks)} chunks from {len(files)} documents; cleanup: "
        + ", ".join(f"{k}={v}" for k, v in totals.items()))

    paths.chunks.parent.mkdir(parents=True, exist_ok=True)
    with paths.chunks.open("w", encoding="utf-8", newline="\n") as f:
        for chunk in all_chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False, sort_keys=True) + "\n")

    over_cap = [c.chunk_id for c in all_chunks if c.n_tokens > CHUNK_MODEL_MAX_TOKENS]     # would be truncated by the model
    whole_sentence = [c.chunk_id for c in all_chunks if CHUNK_MAX_TOKENS < c.n_tokens <= CHUNK_MODEL_MAX_TOKENS]
    summary = {
        "pipeline_version": PIPELINE_VERSION,
        "dataset_version": read_json(paths.manifest)["dataset_version"] if paths.manifest.is_file() else None,
        "tokenizer": EMBED_MODEL,
        "n_chunks": len(all_chunks),
        "n_boilerplate": sum(c.kind == "boilerplate" for c in all_chunks),
        "n_ocr": sum(c.ocr for c in all_chunks),
        "n_page_sections": sum(c.section_source == "page" for c in all_chunks),
        "cleanup": totals,
        "max_tokens": max(c.n_tokens for c in all_chunks),
        "over_cap": over_cap,
        "kept_whole_sentence_above_cap": whole_sentence,
        "docs": per_doc,
    }
    archived = archive_manifest_if_changed(
        paths.summary, summary, paths.summary_dir, version_key="pipeline_version", prefix="chunks-manifest")
    if archived:
        log(f"previous chunks manifest moved to {archived}")
    write_json(paths.summary, summary)
    return summary
