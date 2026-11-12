"""OCR for the pages `ingest` could not read. Run on demand: `python main.py ocr`.

Public API: `run_ocr(...)`. It reads `data/manifest.json` (written by `ingest`), OCRs every page listed
in `ocr_required_pages` that has no OCR file yet, and writes `data/ocr/<doc_id>/page-<n>.md`.
The next `ingest` merges those files into the Markdown. Nothing here is imported by `ingest`,
so ingest, CI and everything after it work without Docling installed.

The OCR engine is injected (`OcrEngine`), like the extractors in `extract.py`.
"""

from collections.abc import Callable, Iterator
from pathlib import Path

from .config import IngestPaths
from .meta import load_catalog
from .store import load_ocr_pages, read_json, write_ocr_page

# (pdf path, 1-based page numbers) -> (page number, Markdown) as each page finishes
OcrEngine = Callable[[Path, list[int]], Iterator[tuple[int, str]]]


def run_ocr(
    *,
    paths: IngestPaths = IngestPaths(),
    engine: OcrEngine | None = None,
    only: list[str] | None = None,
    limit: int | None = None,
    log: Callable[[str], None] = print,
) -> dict:
    """OCR the pending pages. Returns {"done": n, "empty": n, "pending": n, "files": n}.

    only:  keep files whose path contains any of these texts.
    limit: stop after this many pages (for a trial run).
    Each page is written as soon as it is done, so an interrupted run resumes where it stopped.
    """
    manifest = read_json(paths.manifest)
    doc_ids = {e.file: e.doc_id for e in load_catalog(paths.doc_meta, paths.data)}

    todo: list[tuple[str, str, list[int]]] = []     # (file, doc_id, pages)
    for file, record in sorted(manifest["files"].items()):
        if only and not any(text in file for text in only):
            continue
        pages = [n for n in record.get("ocr_required_pages", [])
                 if n not in load_ocr_pages(paths.ocr, doc_ids[file])]
        if pages:
            todo.append((file, doc_ids[file], pages))

    if limit is not None:
        todo = _limit_pages(todo, limit)
    pending = sum(len(pages) for _, _, pages in todo)
    log(f"ocr: {pending} pages in {len(todo)} files")
    if not todo:
        return {"done": 0, "empty": 0, "pending": 0, "files": 0}

    engine = engine or _default_engine()
    done = empty = 0
    for file, doc_id, pages in todo:
        log(f"  {file}: pages {pages}")
        for number, text in engine(paths.data / file, pages):
            write_ocr_page(paths.ocr, doc_id, number, text)
            done += 1
            empty += not text.strip()
            log(f"    page {number}: {len(text.strip())} chars" + ("  (nothing found)" if not text.strip() else ""))
    return {"done": done, "empty": empty, "pending": pending - done, "files": len(todo)}


def _limit_pages(todo, limit):
    out = []
    for file, doc_id, pages in todo:
        if limit <= 0:
            break
        out.append((file, doc_id, pages[:limit]))
        limit -= len(pages[:limit])
    return out


def _default_engine() -> OcrEngine:
    try:
        return docling_engine()
    except ImportError as exc:
        raise SystemExit("Docling is not installed. Run: pip install -r requirements-ocr.txt") from exc


def docling_engine() -> OcrEngine:
    """Docling on CPU, full-page OCR. Models load once and are reused for every page."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = True
    options.ocr_options.force_full_page_ocr = True     # these pages have no usable text layer
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})

    def engine(pdf: Path, pages: list[int]) -> Iterator[tuple[int, str]]:
        for number in pages:
            result = converter.convert(pdf, page_range=(number, number))
            yield number, result.document.export_to_markdown()

    return engine
