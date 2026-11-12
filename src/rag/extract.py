"""Raw file -> list of Pages (Markdown per page). Extraction only: no cleaning, no dedup.

Every extractor has the same shape, `Extractor = (Path) -> list[Page]`, and `default_extractors()`
maps a file kind to one. Supporting a new format means writing one function and adding one
registry entry; nothing else in ingest changes.

Extractors must be top-level functions so they can run in worker processes.
"""

from collections.abc import Callable
from pathlib import Path

from .config import MIN_CHARS_PER_PAGE
from .models import BLANK, OCR_REQUIRED, OK, Page

Extractor = Callable[[Path], list[Page]]


def default_extractors() -> dict[str, Extractor]:
    return {"pdf": extract_pdf, "html": extract_html}


# --- PDF ----------------------------------------------------------------------

def extract_pdf(path: Path) -> list[Page]:
    """One Page per PDF page. Pages with too little text are flagged, not converted.

    Layout-aware Markdown (tables stay tables) via pymupdf4llm. Its built-in OCR is off on
    purpose: scanned pages are left to the separate `ocr` command.
    """
    import pymupdf
    import pymupdf4llm

    with pymupdf.open(path) as doc:
        stats = [(len(p.get_text().strip()), len(p.get_images(full=True))) for p in doc]
        readable = [i for i, (chars, _) in enumerate(stats) if chars >= MIN_CHARS_PER_PAGE]
        markdown: dict[int, str] = {}
        if readable:
            chunks = pymupdf4llm.to_markdown(
                doc, pages=readable, page_chunks=True, use_ocr=False, show_progress=False
            )
            if len(chunks) != len(readable):
                raise RuntimeError(f"pymupdf4llm returned {len(chunks)} pages for {len(readable)} requested")
            markdown = {i: c["text"] for i, c in zip(readable, chunks)}

    pages = []
    for i, (chars, images) in enumerate(stats):
        if i in markdown:
            status = OK
        else:
            status = OCR_REQUIRED if images else BLANK
        pages.append(Page(number=i + 1, text=markdown.get(i, ""), n_chars=chars, n_images=images, status=status))
    return pages


# --- HTML ---------------------------------------------------------------------

# Never content: scripts, widgets, and site chrome shared by every listing page.
_DROP_TAGS = ("script", "style", "noscript", "template", "svg", "iframe", "canvas", "button",
              "input", "select", "textarea", "nav", "footer", "aside", "form")
_HEADINGS = {f"h{n}": "#" * n for n in range(1, 7)}
_BLOCKS = {"p", "div", "section", "article", "main", "header", "dl", "dt", "dd", "figure",
           "figcaption", "blockquote", "address", "span", "a", "ul", "ol", "li", "table"}


def extract_html(path: Path) -> list[Page]:
    """A listing page as a single Page of Markdown: headings, paragraphs, lists and tables."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(_read_html(path), "html.parser")
    root = soup.find("main") or soup.body or soup
    for el in root.find_all(_DROP_TAGS):
        el.decompose()
    if root.name != "main":           # without <main>, the page header is chrome too
        for el in root.find_all("header"):
            el.decompose()
    for el in root.find_all(attrs={"hidden": True}) + root.find_all(attrs={"aria-hidden": "true"}):
        el.decompose()

    writer = _MarkdownWriter()
    writer.walk(root)
    text = writer.render()
    return [Page(number=1, text=text, n_chars=len(text), status=OK if text else BLANK)]


def _read_html(path: Path) -> str:
    from bs4 import BeautifulSoup
    from charset_normalizer import from_bytes

    raw = path.read_bytes()
    best = from_bytes(raw).best()
    html = str(best) if best else raw.decode("utf-8", errors="replace")
    # A Chrome "view-source:" save wraps every source line in <td class="line-content">; unwrap it.
    if "line-content" in html:
        cells = BeautifulSoup(html, "html.parser").select("td.line-content")
        if cells:
            return "\n".join(c.get_text() for c in cells)
    return html


class _MarkdownWriter:
    """Walks a cleaned HTML tree and collects Markdown blocks."""

    def __init__(self) -> None:
        self._blocks: list[str] = []
        self._buffer: list[str] = []

    def walk(self, node) -> None:
        from bs4 import NavigableString

        for child in node.children:
            if isinstance(child, NavigableString):
                if type(child) is NavigableString:        # skips comments and doctypes
                    self._buffer.append(str(child))
                continue
            name = child.name
            if name in _HEADINGS:
                self._emit(f"{_HEADINGS[name]} {_inline(child)}")
            elif name == "table":
                self._emit(_table(child))
            elif name == "li":
                self._emit(f"- {_inline(child)}")
            elif name == "br":
                self._flush()
            elif name in _BLOCKS and child.find(["h1", "h2", "h3", "h4", "h5", "h6", "table", "li"]):
                self._flush()
                self.walk(child)
                self._flush()
            else:                                          # leaf block or inline run
                self._buffer.append(" " + child.get_text(" ") + " ")
                if name in _BLOCKS:
                    self._flush()

    def render(self) -> str:
        self._flush()
        blocks: list[str] = []
        for block in self._blocks:
            if not blocks or block != blocks[-1]:          # skip repeats from responsive markup
                blocks.append(block)
        out = blocks[:1]
        for prev, block in zip(blocks, blocks[1:]):
            tight = prev.startswith("- ") and block.startswith("- ")
            out.append(("\n" if tight else "\n\n") + block)
        return "".join(out).strip()

    def _flush(self) -> None:
        line = " ".join("".join(self._buffer).split())
        self._buffer = []
        if line:
            self._blocks.append(line)

    def _emit(self, block: str) -> None:
        self._flush()
        if block.strip():
            self._blocks.append(block)


def _inline(el) -> str:
    return " ".join(el.get_text(" ").split())


def _table(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_inline(c).replace("|", "\\|") for c in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(r) + " |" for r in rows]
    lines.insert(1, "|" + "---|" * width)
    return "\n".join(lines)
