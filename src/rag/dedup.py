"""Find documents that duplicate another one.

Public API: `find_duplicates(docs)` -> {dropped doc_id: Duplicate}. It never mutates its input,
and the choice of which copy survives is deterministic (sorted by doc_id).
"""

import hashlib
import re
from dataclasses import dataclass

from .config import NEAR_DUP_JACCARD, SHINGLE_WORDS
from .models import LogicalDoc

_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Duplicate:
    of: str            # doc_id that is kept instead
    kind: str          # "exact_duplicate" or "near_duplicate"
    similarity: float


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_duplicates(docs: list[LogicalDoc], threshold: float = NEAR_DUP_JACCARD) -> dict[str, Duplicate]:
    ordered = sorted(docs, key=lambda d: d.doc_id)
    kept: list[tuple[LogicalDoc, str, set[str]]] = []
    dropped: dict[str, Duplicate] = {}

    for doc in ordered:
        text = doc.text
        digest = content_hash(text)
        shingles = _shingles(text)
        match = _first_match(doc, digest, shingles, kept, threshold)
        if match:
            dropped[doc.doc_id] = match
        else:
            kept.append((doc, digest, shingles))
    return dropped


def _first_match(doc, digest, shingles, kept, threshold) -> Duplicate | None:
    for other, other_digest, other_shingles in kept:
        if doc.version_of and doc.version_of == other.version_of:
            continue                      # versions of one file are related on purpose
        if digest == other_digest:
            return Duplicate(other.doc_id, "exact_duplicate", 1.0)
        similarity = _jaccard(shingles, other_shingles)
        if similarity > threshold:
            return Duplicate(other.doc_id, "near_duplicate", round(similarity, 3))
    return None


def _shingles(text: str) -> set[str]:
    words = _WORD.findall(text.lower())
    if len(words) < SHINGLE_WORDS:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + SHINGLE_WORDS]) for i in range(len(words) - SHINGLE_WORDS + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
