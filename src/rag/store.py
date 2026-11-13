"""Everything ingest persists or reads back, in one place.

- Markdown documents with a YAML front-matter block (`write_markdown` / `read_markdown`)
- OCR text for scanned pages (`load_ocr_pages`)
- the extraction cache (`load_cached_pages` / `save_cached_pages`)
- the manifest and the audit log (`write_json`, `write_jsonl`)

Later phases read documents through `read_markdown`, so the on-disk format has one owner.
"""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml

from .models import OK, Page

FRONT_MATTER = "---"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# --- Markdown documents -------------------------------------------------------

def write_markdown(path: Path, front_matter: dict, pages: list[Page]) -> None:
    """Front matter, then each readable page under a `<!-- page N -->` marker."""
    head = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True, width=1000).strip()
    body = "\n\n".join(f"<!-- page {p.number} -->\n\n{p.text}" for p in pages if p.status == OK and p.text.strip())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{FRONT_MATTER}\n{head}\n{FRONT_MATTER}\n\n{body}\n", encoding="utf-8", newline="\n")


def read_markdown(path: Path) -> tuple[dict, str]:
    """(front matter, body) of a file written by `write_markdown`."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith(FRONT_MATTER + "\n"):
        raise ValueError(f"{path}: missing front matter")
    head, _, body = text[len(FRONT_MATTER) + 1:].partition(f"\n{FRONT_MATTER}\n")
    return yaml.safe_load(head), body.lstrip("\n")


def remove_stale_markdown(md_dir: Path, keep: set[str]) -> list[str]:
    """Delete `.md` files whose doc_id is no longer produced. Returns the removed doc_ids."""
    removed = []
    for path in sorted(md_dir.glob("*.md")):
        if path.stem not in keep:
            path.unlink()
            removed.append(path.stem)
    return removed


# --- OCR text -----------------------------------------------------------------

def load_ocr_pages(ocr_dir: Path, file_doc_id: str) -> dict[int, str]:
    """{page number: Markdown} produced earlier by the `ocr` command for this file.

    A page whose OCR found no text is present with an empty string: it was tried, so it is resolved.
    """
    folder = ocr_dir / file_doc_id
    return {
        int(path.stem.split("-")[1]): path.read_text(encoding="utf-8").strip()
        for path in sorted(folder.glob("page-*.md")) if folder.is_dir()
    }


def write_ocr_page(ocr_dir: Path, file_doc_id: str, page: int, text: str) -> None:
    path = ocr_dir / file_doc_id / f"page-{page}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n" if text.strip() else "", encoding="utf-8", newline="\n")


# --- extraction cache ---------------------------------------------------------

def load_cached_pages(cache_dir: Path, key: str) -> list[Page] | None:
    path = cache_dir / f"{key}.json"
    if not path.is_file():
        return None
    return [Page(**p) for p in json.loads(path.read_text(encoding="utf-8"))]


def save_cached_pages(cache_dir: Path, key: str, pages: list[Page]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"{key}.json").write_text(json.dumps([asdict(p) for p in pages]), encoding="utf-8")


# --- manifest and audit -------------------------------------------------------

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def archive_manifest_if_changed(
    current: Path, new: dict, archive_dir: Path, *, version_key: str = "extract_version", prefix: str = "manifest",
) -> Path | None:
    """Move the existing file to `archive_dir/<prefix>-<version>-<hash>.json` if `new` differs.

    The old file is moved, not rewritten. An identical re-run archives nothing. `version` is read from
    the old file (`extract_version` for ingest, `pipeline_version` for the chunk manifest).
    """
    if not current.is_file():
        return None
    old_text = current.read_bytes()
    if json.loads(old_text) == json.loads(json.dumps(new)):
        return None
    version = json.loads(old_text).get(version_key, "unknown")
    target = archive_dir / f"{prefix}-{version}-{hashlib.sha256(old_text).hexdigest()[:8]}.json"
    archive_dir.mkdir(parents=True, exist_ok=True)
    current.replace(target)
    return target


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (json.dumps(e, ensure_ascii=False, sort_keys=True) for e in events)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
