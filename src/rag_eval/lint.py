"""Check the test set against the current chunks. Public API: `lint`.

An evidence quote must sit in exactly one expected document and in no other document.
The search string is the one retrieval uses, `embed_prefix` plus the chunk text, so a heading
counts. `must` groups are AND; the strings inside a group are OR, and one of them must appear in a
chunk that contains an evidence quote. Chunk ids are resolved here and are not stored in the
test set. A no-answer case has no evidence, no `must`, and the abstain sentence as its reference.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from src.rag.answer import ABSTAIN
from src.rag.config import CHUNKS, EVALS_DIR
from src.rag.meta import DOC_TYPES
from src.rag.store import read_jsonl

KINDS = (
    "exact", "paraphrase", "similar-doc", "outdated-version",
    "no-answer", "multi-chunk", "fund-vs-listing",
)
MIN_CASES = 2
TESTSET = EVALS_DIR / "testset.json"


@dataclass(frozen=True)
class LintResult:
    errors: tuple[str, ...]
    chunk_ids: dict[str, tuple[str, ...]]

    @property
    def ok(self) -> bool:
        return not self.errors


def lint(cases: list[dict], chunks: list[dict]) -> LintResult:
    """Errors, and the evidence chunk ids for every case that fully resolved."""
    by_doc: dict[str, list[dict]] = {}
    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        if doc_id:
            by_doc.setdefault(doc_id, []).append(chunk)

    errors: list[str] = []
    counts: dict[str, int] = {}
    seen: set[str] = set()
    clean: list[dict] = []
    for index, case in enumerate(cases):
        case_errors, case_id, kind = _shape(case, index, seen)
        errors.extend(case_errors)
        if kind in KINDS:
            counts[kind] = counts.get(kind, 0) + 1
        if not case_errors and case_id is not None:
            clean.append(case)
    for kind in sorted(counts):
        count = counts[kind]
        if count < MIN_CASES:
            errors.append(f"kind {kind!r} has {count} {_cases(count)}, need at least {MIN_CASES}")

    resolved: dict[str, tuple[str, ...]] = {}
    for case in clean:
        if case["kind"] == "no-answer":
            source_errors = _known_sources(case, by_doc)
            errors.extend(source_errors)
            if not source_errors:
                resolved[case["id"]] = ()
            continue
        ids, case_errors = _resolve(case, by_doc)
        errors.extend(case_errors)
        if not case_errors:
            resolved[case["id"]] = tuple(ids)
    return LintResult(tuple(errors), resolved)


def run(testset: Path = TESTSET, chunks_path: Path = CHUNKS) -> int:
    """Print the errors. Returns 0 when the test set lints, 1 otherwise."""
    cases = json.loads(testset.read_text(encoding="utf-8"))
    result = lint(cases, read_jsonl(chunks_path))
    for error in result.errors:
        print(error)
    print(f"lint: {len(cases)} cases, {len(result.errors)} {_errs(len(result.errors))}")
    return 0 if result.ok else 1


def _shape(case: dict, index: int, seen: set[str]) -> tuple[list[str], str | None, str | None]:
    if not isinstance(case, dict):
        return [f"case {index}: not an object"], None, None
    case_id = case.get("id")
    where = case_id if isinstance(case_id, str) and case_id else f"case {index}"
    errors: list[str] = []
    if not isinstance(case_id, str) or not case_id:
        errors.append(f"{where}: id is missing")
    elif case_id in seen:
        errors.append(f"{where}: duplicate id")
    else:
        seen.add(case_id)
    kind = case.get("kind")
    if kind not in KINDS:
        errors.append(f"{where}: kind {kind!r} is not one of {', '.join(KINDS)}")
        kind = None
    if not isinstance(case.get("question"), str) or not case["question"].strip():
        errors.append(f"{where}: question is missing")
    if not isinstance(case.get("reference"), str) or not case["reference"].strip():
        errors.append(f"{where}: reference is missing")
    elif kind == "no-answer" and case["reference"] != ABSTAIN:
        errors.append(f"{where}: reference must be {ABSTAIN!r}")
    errors.extend(_source_shape(case, where, kind))
    errors.extend(_evidence_shape(case, where, kind))
    errors.extend(_doc_type_shape(case, where))
    return errors, (case_id if isinstance(case_id, str) and case_id else None), kind


def _source_shape(case: dict, where: str, kind: str | None) -> list[str]:
    if "source" not in case:
        return [f"{where}: source is missing"]
    source = case["source"]
    if source is None:
        return [] if kind == "no-answer" else [f"{where}: source is missing"]
    if isinstance(source, str) and source:
        return []
    if isinstance(source, list) and source and all(isinstance(item, str) and item for item in source):
        return []
    return [f"{where}: source must be a document id, a list of ids, or null for a no-answer case"]


def _evidence_shape(case: dict, where: str, kind: str | None) -> list[str]:
    evidence, must = case.get("evidence"), case.get("must")
    if kind == "no-answer":
        errors = []
        if evidence:
            errors.append(f"{where}: a no-answer case has no evidence")
        if must:
            errors.append(f"{where}: a no-answer case has no must")
        return errors
    errors = []
    if not isinstance(evidence, list) or not evidence or not all(isinstance(q, str) and q for q in evidence):
        errors.append(f"{where}: evidence must be a list of quotes")
    if not isinstance(must, list) or not must or not all(_group_ok(group) for group in must):
        errors.append(f"{where}: must must be a list of groups, each a non-empty list of strings")
    return errors


def _group_ok(group: object) -> bool:
    return isinstance(group, list) and bool(group) and all(isinstance(item, str) and item for item in group)


def _doc_type_shape(case: dict, where: str) -> list[str]:
    if "doc_type" not in case:
        return []
    value = case["doc_type"]
    types = [value] if isinstance(value, str) else value
    if not isinstance(types, list) or not types or not all(isinstance(item, str) for item in types):
        return [f"{where}: doc_type must be a type or a list of types"]
    unknown = [item for item in types if item not in DOC_TYPES]
    if unknown:
        return [f"{where}: doc_type {unknown[0]!r} is not one of {', '.join(DOC_TYPES)}"]
    return []


def _known_sources(case: dict, by_doc: dict[str, list[dict]]) -> list[str]:
    errors = []
    for doc_id in _ids(case.get("source")):
        if doc_id not in by_doc:
            errors.append(f"{case['id']}: source {doc_id!r} is not a document in the chunks")
    return errors


def _resolve(case: dict, by_doc: dict[str, list[dict]]) -> tuple[list[str], list[str]]:
    errors = _known_sources(case, by_doc)
    if errors:
        return [], errors
    expected = _ids(case["source"])
    ids: list[str] = []
    seen: set[str] = set()
    evidence_chunks: list[dict] = []
    used: set[str] = set()
    for quote in case["evidence"]:
        found = [doc_id for doc_id, docs in by_doc.items() if any(quote in _hay(chunk) for chunk in docs)]
        inside = [doc_id for doc_id in found if doc_id in expected]
        outside = [doc_id for doc_id in found if doc_id not in expected]
        shown = _show(quote)
        if outside or len(inside) != 1:
            if outside:
                errors.append(f"{case['id']}: evidence is also in {', '.join(outside)}: {shown}")
            if len(inside) != 1:
                where = ", ".join(inside) if inside else "no document"
                errors.append(
                    f"{case['id']}: evidence is in {where}, not exactly one of {', '.join(expected)}: {shown}"
                )
            continue
        used.add(inside[0])
        for chunk in by_doc[inside[0]]:
            if quote in _hay(chunk) and chunk["chunk_id"] not in seen:
                seen.add(chunk["chunk_id"])
                ids.append(chunk["chunk_id"])
                evidence_chunks.append(chunk)
    if errors:
        return ids, errors
    unused = [doc_id for doc_id in expected if doc_id not in used]
    if unused:
        errors.append(f"{case['id']}: {', '.join(unused)} contains none of the evidence")
    if case["kind"] == "multi-chunk" and len(ids) < 2:
        landed = ids[0] if ids else "no chunk"
        errors.append(f"{case['id']}: multi-chunk evidence lands in {landed}")
    for group in case["must"]:
        if any(option in _hay(chunk) for option in group for chunk in evidence_chunks):
            continue
        options = ", ".join(repr(option) for option in group)
        where = ", ".join(chunk["chunk_id"] for chunk in evidence_chunks) or "no chunk"
        errors.append(f"{case['id']}: none of {options} is in the evidence chunks ({where})")
    return ids, errors


def _hay(chunk: dict) -> str:
    """The string retrieval searches: the heading prefix, then the chunk text."""
    prefix = chunk.get("embed_prefix") or ""
    text = chunk.get("text") or ""
    return f"{prefix}\n{text}" if prefix else text


def _ids(source: object) -> list[str]:
    if source is None:
        return []
    if isinstance(source, str):
        return [source]
    if isinstance(source, list):
        return [item for item in source if isinstance(item, str)]
    return []


def _show(quote: str) -> str:
    text = " ".join(quote.split())
    return text if len(text) <= 80 else text[:77] + "..."


def _cases(count: int) -> str:
    return "case" if count == 1 else "cases"


def _errs(count: int) -> str:
    return "error" if count == 1 else "errors"


if __name__ == "__main__":
    sys.exit(run())
