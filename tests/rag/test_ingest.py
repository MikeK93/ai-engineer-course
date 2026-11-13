"""End-to-end ingest with fake extractors and a temp folder: no PDFs, no models."""

import pytest

from src.rag.config import IngestPaths
from src.rag.ingest import ingest
from src.rag.models import OCR_REQUIRED, OK, Page
from src.rag.store import read_markdown

CATALOG = """
- {file: pdfs/plain.pdf, title: Plain, doc_type: listing, as_of: 2021}
- {file: pdfs/copy.pdf, title: Copy, doc_type: listing, as_of: 2021}
- file: pdfs/om.pdf
  title: OM
  doc_type: fund_om
  versions:
    - {suffix: original, start: 1, as_of: 2020-12-31}
    - {suffix: addendum-1, start: 3, as_of: 2021-12-23, replaces: terms}
- {file: pdfs/scan.pdf, title: Scan, doc_type: other, as_of: 2019}
- {file: pdfs/broken.pdf, title: Broken, doc_type: other, as_of: 2019}
"""

BODY = " ".join(f"alpha{i}" for i in range(120))
FILES = {
    "plain": [BODY],
    "copy": [BODY],
    "om": ["Overview of the fund. " * 20, "Fees and terms. " * 20, "ADDENDUM No. 1\n\nNew terms apply. " * 10],
    "scan": ["Cover page with enough readable words in it. " * 5, None],  # None = scanned page
    "broken": None,
}


def fake_pdf(path):
    spec = FILES[path.stem]
    if spec is None:
        raise RuntimeError("corrupt file")
    return [Page(number=i, text=t or "", n_chars=len(t or ""), n_images=0 if t else 1, status=OK if t else OCR_REQUIRED)
            for i, t in enumerate(spec, 1)]


@pytest.fixture
def paths(tmp_path):
    for name in FILES:
        (tmp_path / "pdfs").mkdir(exist_ok=True)
        (tmp_path / "pdfs" / f"{name}.pdf").write_bytes(name.encode())
    (tmp_path / "doc_meta.yaml").write_text(CATALOG, encoding="utf-8")
    return IngestPaths(
        data=tmp_path, doc_meta=tmp_path / "doc_meta.yaml", md=tmp_path / "md", ocr=tmp_path / "ocr",
        manifest=tmp_path / "manifest.json", manifest_dir=tmp_path / "manifests",
        audit_dir=tmp_path / "audit", cache=tmp_path / "cache",
    )


def run(paths, **kw):
    return ingest(paths=paths, extractors={"pdf": fake_pdf}, log=lambda _: None, **kw)


def test_ingest_end_to_end(paths):
    manifest = run(paths)

    ids = {d["doc_id"] for d in manifest["docs"]}
    assert ids == {"pdfs__om@original", "pdfs__om@addendum-1", "pdfs__copy", "pdfs__scan"}
    assert manifest["duplicates"]["pdfs__plain"]["of"] == "pdfs__copy"   # first by doc_id wins
    assert manifest["files"]["pdfs/broken.pdf"]["status"] == "error"
    assert manifest["files"]["pdfs/scan.pdf"]["ocr_required_pages"] == [2]

    front, body = read_markdown(paths.md / "pdfs__om@addendum-1.md")
    assert (front["as_of"], front["version_of"], front["pages"]) == ("2021-12-23", "pdfs__om", "3")
    assert "ADDENDUM No. 1" in body and "Overview of the fund" not in body
    assert sorted(p.name for p in paths.md.glob("*.md")) == sorted(f"{i}.md" for i in ids)


def test_audit_file_per_run_and_old_manifest_moved_when_it_changes(paths, monkeypatch):
    from datetime import datetime, timezone

    def at(h):
        return lambda: datetime(2026, 11, 12, h, 30, 5, tzinfo=timezone.utc)

    run(paths, now=at(8))
    first = paths.manifest.read_text()
    run(paths, now=at(9))                                   # identical result: nothing archived
    assert not paths.manifest_dir.exists()
    assert sorted(p.name for p in paths.audit_dir.glob("*.jsonl")) == [
        "audit-20261112T083005Z.jsonl", "audit-20261112T093005Z.jsonl"]

    monkeypatch.setattr("src.rag.ingest.EXTRACT_VERSION", "extract-vNext")
    run(paths, now=at(10))                                  # new extract version: old manifest is moved
    [archived] = paths.manifest_dir.glob("manifest-*.json")
    assert archived.read_text() == first and archived.name.startswith("manifest-extract-v")
    assert '"extract-vNext"' in paths.manifest.read_text()


def test_ocr_text_fills_scanned_pages(paths):
    (paths.ocr / "pdfs__scan").mkdir(parents=True)
    (paths.ocr / "pdfs__scan" / "page-2.md").write_text("Text recovered by OCR from the scan.", encoding="utf-8")
    manifest = run(paths)
    front, body = read_markdown(paths.md / "pdfs__scan.md")
    assert "recovered by OCR" in body and front["ocr_pages"] == [2]
    assert manifest["files"]["pdfs/scan.pdf"]["ocr_required_pages"] == []


def test_second_run_is_cached_and_output_is_identical(paths):
    first = run(paths)
    calls = []
    second = ingest(paths=paths, extractors={"pdf": lambda p: calls.append(p) or fake_pdf(p)}, log=lambda _: None)
    assert [p.stem for p in calls] == ["broken"]       # only the failed file is retried
    assert second == first


def test_full_flag_ignores_cache_and_stale_markdown_is_removed(paths):
    run(paths)
    (paths.md / "pdfs__gone.md").write_text("old", encoding="utf-8")
    calls = []
    ingest(paths=paths, extractors={"pdf": lambda p: calls.append(p) or fake_pdf(p)}, log=lambda _: None, full=True)
    assert len(calls) == len(FILES)
    assert not (paths.md / "pdfs__gone.md").exists()


# --- ocr command --------------------------------------------------------------

def fake_engine(text_for):
    calls = []

    def engine(pdf, pages):
        calls.append((pdf.stem, list(pages)))
        for n in pages:
            yield n, text_for(n)

    engine.calls = calls
    return engine


def test_ocr_writes_pending_pages_then_ingest_merges_them(paths):
    from src.rag.ocr import run_ocr

    run(paths)                                           # scan.pdf page 2 is ocr_required
    engine = fake_engine(lambda n: f"Recovered text of page {n} from the scan.")
    report = run_ocr(paths=paths, engine=engine, log=lambda _: None)
    assert report == {"done": 1, "empty": 0, "pending": 0, "files": 1}
    assert engine.calls == [("scan", [2])]
    assert (paths.ocr / "pdfs__scan" / "page-2.md").read_text().startswith("Recovered text of page 2")

    run_ocr(paths=paths, engine=engine, log=lambda _: None)   # nothing left to do: engine not called again
    assert len(engine.calls) == 1

    manifest = run(paths)
    assert manifest["files"]["pdfs/scan.pdf"]["ocr_required_pages"] == []
    assert manifest["files"]["pdfs/scan.pdf"]["ocr_pages"] == [2]


def test_ocr_that_finds_nothing_resolves_the_page_as_blank(paths):
    from src.rag.ocr import run_ocr

    run(paths)
    report = run_ocr(paths=paths, engine=fake_engine(lambda n: ""), log=lambda _: None)
    assert report["empty"] == 1
    manifest = run(paths)
    record = manifest["files"]["pdfs/scan.pdf"]
    assert record["ocr_required_pages"] == [] and record["blank_pages"] == [2] and record["ocr_pages"] == []


def test_ocr_only_and_limit(paths):
    from src.rag.ocr import run_ocr

    run(paths)
    engine = fake_engine(lambda n: "x" * 30)
    assert run_ocr(paths=paths, engine=engine, only=["nothing-matches"], log=lambda _: None)["files"] == 0
    assert run_ocr(paths=paths, engine=engine, limit=0, log=lambda _: None)["files"] == 0
    assert engine.calls == []


def test_garbled_page_is_sent_to_ocr_and_filled_by_the_ocr_text(tmp_path):
    from src.rag.ingest import _merge_ocr

    garbled = Page(number=2, text="\uf04d\uf05f\uf060\uf06a " * 30, n_chars=120)
    fine = Page(number=1, text="Readable text of the first page.", n_chars=32)
    pending = _merge_ocr([fine, garbled], {})
    assert [(p.number, p.status, p.text) for p in pending] == [(1, OK, fine.text), (2, OCR_REQUIRED, "")]
    done = _merge_ocr([fine, garbled], {2: "Financial statements, restored."})
    assert (done[1].status, done[1].source, done[1].text) == (OK, "ocr", "Financial statements, restored.")
