"""The document catalog: `data/doc_meta.yaml`, one entry per corpus file.

`load_catalog()` is the only entry point. It validates everything up front and raises one
`CatalogError` that lists every problem, so a bad file name or date is fixed in one pass.
"""

import datetime
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import DATA, DOC_META

DOC_TYPES = ("listing", "single_asset_om", "fund_om", "other")
KINDS = {"pdfs": "pdf", "html": "html"}          # folder under data/ -> kind
_AS_OF = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class VersionSpec:
    """One logical version of a file, for example the original memorandum and its addendum."""

    suffix: str
    start: int | str          # physical page number, or a heading that starts the version
    as_of: str
    replaces: str | None = None


@dataclass(frozen=True)
class DocEntry:
    file: str                 # "pdfs/<name>" or "html/<name>", relative to data/
    title: str
    doc_type: str
    as_of: str | None         # None only when `versions` carries the dates
    source_url: str | None = None
    versions: tuple[VersionSpec, ...] = ()
    path: Path = Path()       # absolute path of the file

    @property
    def kind(self) -> str:
        return KINDS[self.file.split("/", 1)[0]]

    @property
    def doc_id(self) -> str:
        """Stable, file-system safe id derived from the path: `pdfs__gs01_33_Unit_Multifamily`."""
        folder, name = self.file.split("/", 1)
        return f"{folder}__{re.sub(r'[^A-Za-z0-9._-]+', '_', Path(name).stem).strip('_')}"


def load_catalog(meta_path: Path = DOC_META, data_dir: Path = DATA) -> list[DocEntry]:
    """Parse and validate the catalog. Entries come back sorted by file."""
    raw = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or []
    problems: list[str] = []
    entries: list[DocEntry] = []

    for i, item in enumerate(raw, 1):
        label = f"entry {i} ({item.get('file', '?') if isinstance(item, dict) else item!r})"
        entry = _parse_entry(item, label, data_dir, problems)
        if entry:
            entries.append(entry)

    _check_unique(entries, problems)
    _check_orphans({i.get("file") for i in raw if isinstance(i, dict)}, data_dir, problems)

    if problems:
        raise CatalogError(f"{meta_path.name} has {len(problems)} problem(s):\n" + "\n".join(f" - {p}" for p in problems))
    return sorted(entries, key=lambda e: e.file)


def _as_of(value, label: str, problems: list[str]) -> str | None:
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, (str, int)) and _AS_OF.match(str(value)):
        return str(value)
    problems.append(f"{label}: as_of {value!r} must be YYYY, YYYY-MM or YYYY-MM-DD")
    return None


def _parse_entry(item, label: str, data_dir: Path, problems: list[str]) -> DocEntry | None:
    if not isinstance(item, dict):
        problems.append(f"{label}: expected a mapping")
        return None
    start = len(problems)

    file = item.get("file", "")
    folder = file.split("/", 1)[0] if "/" in file else ""
    if folder not in KINDS:
        problems.append(f"{label}: file must start with one of {sorted(KINDS)}/")
    elif not (data_dir / file).is_file():
        problems.append(f"{label}: no such file under {data_dir}")

    for key in ("title", "doc_type"):
        if not item.get(key):
            problems.append(f"{label}: missing {key}")
    if item.get("doc_type") and item["doc_type"] not in DOC_TYPES:
        problems.append(f"{label}: doc_type {item['doc_type']!r} must be one of {DOC_TYPES}")
    if folder == "html" and not item.get("source_url"):
        problems.append(f"{label}: html entries need source_url")

    versions = tuple(_parse_versions(item.get("versions") or [], label, problems))
    as_of = None
    if versions:
        if "as_of" in item:
            problems.append(f"{label}: put as_of on each version, not on the entry")
    elif "as_of" not in item:
        problems.append(f"{label}: missing as_of (or a versions list)")
    else:
        as_of = _as_of(item["as_of"], label, problems)

    if len(problems) > start:
        return None
    return DocEntry(
        file=file, title=item["title"], doc_type=item["doc_type"], as_of=as_of,
        source_url=item.get("source_url"), versions=versions, path=data_dir / file,
    )


def _parse_versions(raw: list, label: str, problems: list[str]) -> list[VersionSpec]:
    versions: list[VersionSpec] = []
    for v in raw:
        vlabel = f"{label} version {v.get('suffix', '?') if isinstance(v, dict) else v!r}"
        if not isinstance(v, dict) or not v.get("suffix") or "start" not in v or "as_of" not in v:
            problems.append(f"{vlabel}: needs suffix, start and as_of")
            continue
        as_of = _as_of(v["as_of"], vlabel, problems)
        if as_of:
            versions.append(VersionSpec(str(v["suffix"]), v["start"], as_of, v.get("replaces")))
    suffixes = [v.suffix for v in versions]
    if len(set(suffixes)) != len(suffixes):
        problems.append(f"{label}: version suffixes must be unique")
    return versions


def _check_unique(entries: list[DocEntry], problems: list[str]) -> None:
    for attr in ("file", "doc_id"):
        seen: dict[str, str] = {}
        for e in entries:
            key = getattr(e, attr)
            if key in seen:
                problems.append(f"{e.file}: {attr} {key!r} is already used by {seen[key]}")
            seen[key] = e.file


def _check_orphans(listed: set, data_dir: Path, problems: list[str]) -> None:
    for folder, kind in KINDS.items():
        for path in sorted((data_dir / folder).glob(f"*.{kind}")):
            rel = f"{folder}/{path.name}"
            if rel not in listed:
                problems.append(f"{rel}: file has no entry in the catalog")
