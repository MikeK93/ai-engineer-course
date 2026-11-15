"""Keyword search (BM25). Public API: `Bm25Index`, `tokenize`.

Real-estate questions turn on exact figures and names (`$1,250,000`, `80231`, `9850 East Girard`),
which a vector search blurs. The tokenizer therefore keeps a number whole, with its thousands
separators, decimals, `$` and `%`, instead of cutting it at every punctuation mark.

The index is built in memory from the chunk list in a fraction of a second, so it is never stored.
It reads the same string as the embedder (`embedding_text`).
"""

import re
from collections.abc import Callable

import numpy as np
from rank_bm25 import BM25Okapi

from .embed import embedding_text

# $1,250,000 | 80231 | 5.25% | 34,076 | then plain words (letters and digits, no underscore)
_TOKEN = re.compile(r"\$?\d+(?:[.,]\d+)*%?|[^\W_]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class Bm25Index:
    def __init__(self, chunks: list[dict]):
        self._chunks = chunks
        self._bm25 = BM25Okapi([tokenize(embedding_text(c)) for c in chunks])

    def search(self, query: str, k: int, accept: Callable[[dict], bool] = lambda chunk: True) -> list[tuple[str, float]]:
        """Top `k` (chunk_id, score) among the chunks `accept` allows. The filter is applied before ranking,
        so a filtered-out chunk never takes a place. Chunks sharing no word with the query are not returned."""
        terms = tokenize(query)
        if not terms or not self._chunks:
            return []
        scores = self._bm25.get_scores(terms)
        allowed = np.array([accept(c) for c in self._chunks])
        scores = np.where(allowed, scores, -np.inf)
        best = np.argsort(-scores)[:k]
        return [(self._chunks[i]["chunk_id"], float(scores[i])) for i in best if scores[i] > 0]
