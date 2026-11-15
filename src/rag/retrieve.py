"""Search. Public API: `Retriever.search(query, config, filters, k)`, `load_retriever()`, `rrf_fuse`.

Four configs, each building on the one before:
- `vector`: nearest chunks by meaning (Qdrant)
- `bm25`:   chunks sharing the query's words and figures
- `hybrid`: both lists (top CANDIDATES each), fused by reciprocal rank fusion
- `rerank`: the top CANDIDATES hybrid hits, re-ordered by a cross-encoder, best K kept

Every config applies the same `Filters` before ranking, so a filtered-out chunk never takes a place.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from qdrant_client import QdrantClient

from .bm25 import Bm25Index, tokenize
from .config import CANDIDATES, COLLECTION, K, RRF_K, IndexPaths
from .embed import Embedder
from .index import Filters, open_client
from .store import read_jsonl

CONFIGS = ("vector", "bm25", "hybrid", "rerank")


@dataclass(frozen=True)
class Hit:
    chunk: dict
    score: float
    ranks: dict[str, int] = field(default_factory=dict)    # 1-based rank in each list that contained it


def rrf_fuse(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """Reciprocal rank fusion: an id scores the sum of 1/(k + rank) over the lists it appears in.
    Ties keep the order in which the ids were first seen."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: -item[1])


class Retriever:
    def __init__(self, client: QdrantClient, bm25: Bm25Index, embedder: Embedder, chunks: list[dict],
                 reranker=None, collection: str = COLLECTION, log: Callable[[str], None] = lambda _: None):
        self.client, self.bm25, self.embedder, self.collection = client, bm25, embedder, collection
        self.reranker = reranker
        self.log = log
        self.chunks = {c["chunk_id"]: c for c in chunks}

    def search(self, query: str, config: str = "hybrid", *, filters: Filters = Filters(), k: int = K) -> list[Hit]:
        if config not in CONFIGS:
            raise ValueError(f"unknown config {config!r}; use one of {CONFIGS}")
        self.log(f"search: config={config} k={k} query={query!r}")
        self.log(f"  filters: {filters}")
        if config == "vector":
            return self._hits({"vector": self._vector(query, filters, k)})[:k]
        if config == "bm25":
            return self._hits({"bm25": self._bm25(query, filters, k)})[:k]
        fused = self._hybrid(query, filters)
        if config == "hybrid":
            return fused[:k]
        if self.reranker is None:
            raise ValueError("the rerank config needs a reranker")
        self.log(f"  rerank: cross-encoder scores the top {min(CANDIDATES, len(fused))} hybrid hits, keeps {k}")
        hits = self.reranker.rerank(query, fused[:CANDIDATES], top=k)
        for h in hits:
            self.log(f"    rerank {h.ranks['rerank']}: score {h.score:.2f}, first-stage ranks "
                     f"{ {n: r for n, r in h.ranks.items() if n != 'rerank'} } {h.chunk['chunk_id'][-40:]}")
        return hits

    # --- the lists ------------------------------------------------------------

    def _vector(self, query: str, filters: Filters, n: int) -> list[tuple[str, float]]:
        response = self.client.query_points(
            self.collection, query=self.embedder.embed_query(query), query_filter=filters.to_qdrant(),
            limit=n, with_payload=True)
        found = [(p.payload["chunk_id"], float(p.score)) for p in response.points]
        self.log(f"  vector: query embedded with the bge prefix, Qdrant returned {len(found)} (asked {n}); "
                 f"best {found[0][1]:.3f}" if found else "  vector: no hits")
        return found

    def _bm25(self, query: str, filters: Filters, n: int) -> list[tuple[str, float]]:
        found = self.bm25.search(query, n, filters.accepts)
        self.log(f"  bm25: terms {tokenize(query)} -> {len(found)} hits (asked {n})"
                 + (f"; best {found[0][1]:.2f}" if found else ""))
        return found

    def _hybrid(self, query: str, filters: Filters) -> list[Hit]:
        vector = self._vector(query, filters, CANDIDATES)
        keyword = self._bm25(query, filters, CANDIDATES)
        fused = rrf_fuse([[i for i, _ in vector], [i for i, _ in keyword]])
        both = len({i for i, _ in vector} & {i for i, _ in keyword})
        self.log(f"  hybrid: RRF 1/({RRF_K}+rank) fused {len(vector)} vector + {len(keyword)} bm25 hits "
                 f"into {len(fused)} chunks ({both} found by both)")
        ranks = {"vector": {i: r for r, (i, _) in enumerate(vector, 1)},
                 "bm25": {i: r for r, (i, _) in enumerate(keyword, 1)}}
        return [Hit(self.chunks[i], score, {name: r[i] for name, r in ranks.items() if i in r}) for i, score in fused]

    def _hits(self, lists: dict[str, list[tuple[str, float]]]) -> list[Hit]:
        [(name, ranked)] = lists.items()
        return [Hit(self.chunks[i], score, {name: rank}) for rank, (i, score) in enumerate(ranked, 1)]


def load_retriever(paths: IndexPaths = IndexPaths(), *, embedder: Embedder | None = None,
                   reranker=None, log: Callable[[str], None] = print) -> Retriever:
    """The retriever over the built index: chunks and BM25 from `chunks.jsonl`, vectors from Qdrant."""
    from .rerank import Reranker

    chunks = read_jsonl(paths.chunks)
    log(f"load: {len(chunks)} chunks from {paths.chunks}")
    bm25 = Bm25Index(chunks)
    log("load: BM25 index built in memory")
    client = open_client(paths.index)
    log(f"load: Qdrant opened at {paths.index}")
    return Retriever(client, bm25, embedder or Embedder(cache=paths.embedding_cache, log=log), chunks,
                     reranker=reranker or Reranker(), log=log)
