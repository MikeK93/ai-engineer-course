"""The vector index (embedded Qdrant) and the filters on it. Public API: `build_index`, `open_client`, `Filters`.

The index is rebuilt from `data/chunks.jsonl` and nothing else, and is never committed. One point per
chunk: the vector of `embedding_text(chunk)` and the whole chunk as payload (clean text, not the
embedded string). `as_of_num` (YYYYMMDD) is added to the payload so a date can be filtered as a number.

`Filters` is the single description of what a search may return. It knows how to apply itself to
Qdrant (`to_qdrant`) and to a plain chunk (`accepts`, used by BM25), so the two searches never disagree.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient, models

from .config import COLLECTION
from .embed import Embedder, embedding_text

UPLOAD_BATCH = 256


def as_of_num(as_of: str) -> int:
    """`2021`, `2021-12` or `2021-12-23` as 20210101, 20211201 or 20211223, so dates compare as numbers."""
    parts = [int(p) for p in str(as_of).split("-")] + [1, 1]
    return parts[0] * 10000 + parts[1] * 100 + parts[2]


@dataclass(frozen=True)
class Filters:
    """What a search may return. By default boilerplate and comparables are left out."""

    doc_types: tuple[str, ...] | None = None    # e.g. ("single_asset_om", "listing"); None = any
    as_of_min: str | None = None                # only documents dated on or after this, e.g. "2024"
    include_boilerplate: bool = False           # disclaimers, tables of contents
    include_skip: bool = False                  # `skip_candidate` chunks: sale / rent comparables

    def accepts(self, chunk: dict) -> bool:
        if self.doc_types is not None and chunk["doc_type"] not in self.doc_types:
            return False
        if self.as_of_min is not None and as_of_num(chunk["as_of"]) < as_of_num(self.as_of_min):
            return False
        if not self.include_boilerplate and chunk["kind"] == "boilerplate":
            return False
        if not self.include_skip and chunk.get("skip_candidate"):
            return False
        return True

    def to_qdrant(self) -> models.Filter | None:
        must, must_not = [], []
        if self.doc_types is not None:
            must.append(models.FieldCondition(key="doc_type", match=models.MatchAny(any=list(self.doc_types))))
        if self.as_of_min is not None:
            must.append(models.FieldCondition(key="as_of_num", range=models.Range(gte=as_of_num(self.as_of_min))))
        if not self.include_boilerplate:
            must_not.append(models.FieldCondition(key="kind", match=models.MatchValue(value="boilerplate")))
        if not self.include_skip:
            must_not.append(models.FieldCondition(key="skip_candidate", match=models.MatchValue(value=True)))
        return models.Filter(must=must or None, must_not=must_not or None) if (must or must_not) else None


def open_client(path: Path | str) -> QdrantClient:
    """The embedded Qdrant at `path`, or in memory for ":memory:". One process at a time may open a folder."""
    if str(path) != ":memory:":
        Path(path).mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(path))
    return QdrantClient(":memory:")


def build_index(chunks: list[dict], embedder: Embedder, client: QdrantClient, *, collection: str = COLLECTION,
                log: Callable[[str], None] = print) -> int:
    """Replace the collection with one point per chunk. Returns the number of points."""
    if not chunks:
        raise ValueError("no chunks to index")
    log(f"index: embedding {len(chunks)} chunks")
    vectors = embedder.embed_documents([embedding_text(c) for c in chunks])

    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection, vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE))
    for start in range(0, len(chunks), UPLOAD_BATCH):
        part = range(start, min(start + UPLOAD_BATCH, len(chunks)))
        client.upsert(collection, points=[
            models.PointStruct(id=i, vector=vectors[i], payload={**chunks[i], "as_of_num": as_of_num(chunks[i]["as_of"])})
            for i in part])
    log(f"index: {len(chunks)} points in '{collection}' "
        f"({embedder.stats['embedded']} embedded, {embedder.stats['cached']} from cache)")
    return len(chunks)
