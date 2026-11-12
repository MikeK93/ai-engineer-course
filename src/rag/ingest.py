"""Ingest: raw PDFs/HTML -> normalized, deduplicated, version-split Markdown in `data/md/`.

Public API: `ingest(...)`. Steps, in order:

1. read and validate the catalog (`doc_meta.yaml`)
2. extract pages from each file (slow; cached by file hash, optionally in parallel)
3. per file: merge OCR text, normalize, split into versions
4. drop duplicates across all documents
5. write Markdown, manifest and audit log

Only step 2 is cached. Steps 3-5 are cheap and run every time, so the Markdown and manifest
depend only on the inputs and the code, never on what an earlier run left behind.

Outputs: `manifest.json` (latest; the previous one is moved to `manifests/` when the new one
differs, never overwritten) and `audit/audit-<UTC timestamp>.jsonl` (one new file per run).
"""

import hashlib
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone

from .config import EXTRACT_VERSION, PIPELINE_VERSION, IngestPaths
from .dedup import content_hash, find_duplicates
from .extract import Extractor, default_extractors
from .meta import DocEntry, load_catalog
from .models import BLANK, OCR_REQUIRED, OK, LogicalDoc, Page
from .normalize import normalize_pages
from .store import (archive_manifest_if_changed, file_sha256, load_cached_pages, load_ocr_pages, remove_stale_markdown,
                    save_cached_pages, write_json, write_jsonl, write_markdown)
from .versions import find_version_markers, split_versions


def ingest(
    *,
    full: bool = False,
    workers: int = 1,
    only: list[str] | None = None,
    paths: IngestPaths = IngestPaths(),
    extractors: dict[str, Extractor] | None = None,
    log: Callable[[str], None] = print,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict:
    """Run the whole ingest and return the manifest that was written.

    full:       ignore the extraction cache and re-extract every file.
    workers:    parallel extraction processes (1 = in this process).
    only:       keep catalog entries whose `file` contains any of these texts (for trial runs).
    extractors: kind -> extractor, to support or fake other formats.
    """
    extractors = extractors or default_extractors()
    entries = load_catalog(paths.doc_meta, paths.data)
    if only:
        entries = [e for e in entries if any(text in e.file for text in only)]
        if not entries:
            raise ValueError(f"--only {only} matches no catalog entry")
    events: list[dict] = []

    hashes = {e.file: file_sha256(e.path) for e in entries}
    extracted, failed = _extract_all(entries, hashes, extractors, paths, full, workers, log)

    docs: list[LogicalDoc] = []
    files: dict[str, dict] = {}
    for entry in entries:
        record = {"raw_hash": hashes[entry.file], "status": "ok", "docs": []}
        files[entry.file] = record
        if entry.file in failed:
            _fail(record, events, entry, failed[entry.file])
            continue
        try:
            file_docs = _prepare(entry, extracted[entry.file], paths, record, events)
        except ValueError as exc:
            _fail(record, events, entry, str(exc))
            continue
        record["docs"] = [d.doc_id for d in file_docs]
        docs.extend(file_docs)

    duplicates = find_duplicates(docs)
    for doc_id, dup in sorted(duplicates.items()):
        events.append({"event": dup.kind, "doc_id": doc_id, "of": dup.of, "similarity": dup.similarity})
    kept = [d for d in docs if d.doc_id not in duplicates]

    return _write_outputs(kept, duplicates, files, paths, events, now, log)


# --- step 2: extraction -------------------------------------------------------

def _cache_key(raw_hash: str) -> str:
    return f"{raw_hash[:32]}-{EXTRACT_VERSION}"


def _extract_all(entries, hashes, extractors, paths, full, workers, log):
    pages: dict[str, list[Page]] = {}
    failed: dict[str, str] = {}
    todo: list[DocEntry] = []
    for e in entries:
        cached = None if full else load_cached_pages(paths.cache, _cache_key(hashes[e.file]))
        if cached is not None:
            pages[e.file] = cached
        else:
            todo.append(e)
    log(f"ingest: {len(entries)} files, {len(entries) - len(todo)} cached, {len(todo)} to extract")

    def finish(entry: DocEntry, result: list[Page] | Exception, started: float) -> None:
        if isinstance(result, Exception):
            failed[entry.file] = f"{type(result).__name__}: {result}"
            log(f"  FAILED {entry.file}: {failed[entry.file]}")
            return
        pages[entry.file] = result
        save_cached_pages(paths.cache, _cache_key(hashes[entry.file]), result)
        log(f"  extracted {entry.file} ({len(result)} pages, {time.time() - started:.1f}s)")

    if workers > 1 and len(todo) > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(extractors[e.kind], e.path): (e, time.time()) for e in todo}
            for future in as_completed(futures):
                entry, started = futures[future]
                finish(entry, future.exception() or future.result(), started)
    else:
        for e in todo:
            started = time.time()
            try:
                result = extractors[e.kind](e.path)
            except Exception as exc:  # one broken file must not stop the corpus
                result = exc
            finish(e, result, started)
    return pages, failed


# --- step 3: per-file preparation ---------------------------------------------

def _prepare(entry: DocEntry, pages: list[Page], paths: IngestPaths, record: dict, events: list[dict]) -> list[LogicalDoc]:
    pages = _merge_ocr(pages, load_ocr_pages(paths.ocr, entry.doc_id))
    pages = normalize_pages(pages)

    record["pages"] = len(pages)
    record["ocr_required_pages"] = [p.number for p in pages if p.status == OCR_REQUIRED]
    record["blank_pages"] = [p.number for p in pages if p.status == BLANK]
    record["ocr_pages"] = [p.number for p in pages if p.source == "ocr"]
    if record["ocr_required_pages"]:
        record["status"] = OCR_REQUIRED
        events.append({"event": "ocr_required", "file": entry.file, "pages": record["ocr_required_pages"]})
    if record["blank_pages"]:
        events.append({"event": "blank_pages", "file": entry.file, "pages": record["blank_pages"]})

    if not any(p.status == OK and p.text.strip() for p in pages):
        raise ValueError("no extractable text (scanned file? run the ocr command)")

    if not entry.versions:
        for page, heading in find_version_markers(pages):
            events.append({"event": "version_marker", "file": entry.file, "page": page, "line": heading})

    docs = split_versions(entry, pages)
    for doc in docs:
        if not doc.text.strip():
            raise ValueError(f"version {doc.doc_id} has no text")
    return docs


def _merge_ocr(pages: list[Page], ocr: dict[int, str]) -> list[Page]:
    return [
        replace(p, text=ocr[p.number], status=OK, source="ocr") if p.status == OCR_REQUIRED and p.number in ocr else p
        for p in pages
    ]


def _fail(record: dict, events: list[dict], entry: DocEntry, message: str) -> None:
    record.update(status="error", error=message)
    events.append({"event": "error", "file": entry.file, "message": message})


# --- step 5: outputs ----------------------------------------------------------

def _write_outputs(kept, duplicates, files, paths, events, now, log) -> dict:
    docs_meta = []
    for doc in sorted(kept, key=lambda d: d.doc_id):
        digest = content_hash(doc.text)
        front = {
            "doc_id": doc.doc_id, "title": doc.title, "source": doc.source, "doc_type": doc.doc_type,
            "as_of": doc.as_of, "source_url": doc.source_url, "version_of": doc.version_of,
            "replaces": doc.replaces, "pages": doc.page_range, "ocr_pages": doc.ocr_pages,
            "content_hash": digest,
        }
        front = {k: v for k, v in front.items() if v not in (None, [])}
        write_markdown(paths.md / f"{doc.doc_id}.md", front, doc.pages)
        docs_meta.append({**front, "chars": len(doc.text), "md": f"{doc.doc_id}.md"})
        events.append({"event": "ingested", "doc_id": doc.doc_id, "chars": len(doc.text)})

    for doc_id in remove_stale_markdown(paths.md, {d.doc_id for d in kept}):
        events.append({"event": "removed_stale", "doc_id": doc_id})

    dataset_version = hashlib.sha256(
        "\n".join(f"{d['doc_id']}:{d['content_hash']}" for d in docs_meta).encode()
    ).hexdigest()[:12]
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "extract_version": EXTRACT_VERSION,
        "dataset_version": dataset_version,
        "docs": docs_meta,
        "files": files,
        "duplicates": {k: vars(v) for k, v in sorted(duplicates.items())},
    }
    archive_manifest_if_changed(paths.manifest, manifest, paths.manifest_dir)
    write_json(paths.manifest, manifest)
    stamp = now().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit_path = paths.audit_dir / f"audit-{stamp}.jsonl"
    write_jsonl(audit_path, events)
    log(f"audit log: {audit_path}")
    return manifest


def summarize(manifest: dict) -> str:
    """One paragraph for the terminal."""
    files = manifest["files"].values()
    errors = sum(f["status"] == "error" for f in files)
    needs_ocr = sum(len(f.get("ocr_required_pages", [])) for f in files)
    return (
        f"{len(manifest['docs'])} documents written, {len(manifest['duplicates'])} duplicates dropped, "
        f"{errors} files failed, {needs_ocr} pages need OCR. dataset_version={manifest['dataset_version']}"
    )
