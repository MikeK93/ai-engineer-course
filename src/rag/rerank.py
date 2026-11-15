"""Re-ordering the best hits with a cross-encoder. Public API: `Reranker`.

A cross-encoder reads the query and one chunk together, which is slower but more exact than comparing
two separate vectors, so it is only run on the few hits that hybrid search already found.
The scorer is injected (`Scorer`), so tests run without downloading the model.
"""

from collections.abc import Callable
from dataclasses import replace

from .config import K, RERANK_MODEL
from .embed import embedding_text
from .retrieve import Hit

# (query, passage) pairs -> one relevance score per pair
Scorer = Callable[[list[tuple[str, str]]], list[float]]


class Reranker:
    def __init__(self, score: Scorer | None = None, model: str = RERANK_MODEL):
        self._score = score
        self.model = model

    def rerank(self, query: str, hits: list[Hit], top: int = K) -> list[Hit]:
        """The `top` hits by cross-encoder score, best first. The first-stage ranks are kept on each hit."""
        if not hits:
            return []
        scores = self._scorer()([(query, embedding_text(h.chunk)) for h in hits])
        ordered = sorted(zip(hits, scores), key=lambda pair: -pair[1])[:top]
        return [replace(h, score=float(s), ranks={**h.ranks, "rerank": i + 1}) for i, (h, s) in enumerate(ordered)]

    def _scorer(self) -> Scorer:
        if self._score is None:
            self._score = cross_encoder_scorer(self.model)
        return self._score


def cross_encoder_scorer(model: str = RERANK_MODEL) -> Scorer:
    from sentence_transformers import CrossEncoder

    encoder = CrossEncoder(model, device="cpu")
    return lambda pairs: [float(s) for s in encoder.predict(pairs, show_progress_bar=False)]
