"""Plain data shared by the ingest modules. No behavior beyond small derived properties."""

from dataclasses import dataclass

OK = "ok"                      # page has usable text
OCR_REQUIRED = "ocr_required"  # almost no text, but the page has images
BLANK = "blank"                # almost no text and no images


@dataclass(frozen=True)
class Page:
    """One physical page. HTML documents are a single page numbered 1."""

    number: int                # 1-based, physical (not the printed page label)
    text: str                  # Markdown; empty unless status is OK
    n_chars: int = 0           # raw characters found on the page, before Markdown
    n_images: int = 0
    n_drawings: int = 0        # vector paths; text converted to outlines shows up here
    status: str = OK
    source: str = "extract"    # "extract" or "ocr"


@dataclass
class LogicalDoc:
    """One searchable document: a whole file, or one version of a file that has an addendum."""

    doc_id: str                # file slug, plus "@<suffix>" for a version
    source: str                # "pdfs/<name>" or "html/<name>"
    title: str
    doc_type: str
    as_of: str                 # YYYY, YYYY-MM or YYYY-MM-DD
    pages: list[Page]
    source_url: str | None = None
    version_of: str | None = None   # file slug shared by all versions of one file
    replaces: str | None = None     # free text: what this version supersedes

    @property
    def text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.status == OK and p.text.strip())

    @property
    def page_range(self) -> str:
        first, last = self.pages[0].number, self.pages[-1].number
        return str(first) if first == last else f"{first}-{last}"

    @property
    def ocr_pages(self) -> list[int]:
        return [p.number for p in self.pages if p.source == "ocr"]