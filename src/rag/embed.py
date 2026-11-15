"""Embeddings with a cache. Public API: `Embedder`, `embedding_text(chunk)`.

`embedding_text` is the one string every search method reads: the chunk's `embed_prefix` (title + section)
followed by its text. The vector index and BM25 both use it, so they cannot drift apart. The payload
stored in the index keeps the clean text.

Vectors are cached in SQLite, keyed by `EMBED_MODEL + "\\n" + text`, so rebuilding the index only embeds
chunks that are new or changed, and changing the model never reuses old vectors. The encoder is injected
(`Encoder`), so tests run without downloading the model.
"""

import hashlib
import sqlite3
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

from .config import BGE_QUERY_PREFIX, EMBED_MODEL, EMBEDDING_CACHE

Vector = list[float]
# texts -> one L2-normalised vector per text
Encoder = Callable[[list[str]], Sequence[Sequence[float]]]

BATCH = 32


def embedding_text(chunk: dict) -> str:
    """What is embedded and BM25-indexed for a chunk: title + section, then the text."""
    return f"{chunk['embed_prefix']}\n{chunk['text']}"


class Embedder:
    def __init__(self, encode: Encoder | None = None, *, cache: Path | None = EMBEDDING_CACHE,
                 model: str = EMBED_MODEL, batch: int = BATCH, log: Callable[[str], None] = print):
        self._encode = encode
        self.model = model
        self.batch = batch
        self.log = log
        self._db = self._open(cache) if cache else None
        self.stats = {"cached": 0, "embedded": 0}

    # --- public ---------------------------------------------------------------

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        """One vector per text. Texts already in the cache are not encoded again."""
        keys = [self._key(t) for t in texts]
        found = self._lookup(set(keys))
        missing = [i for i, k in enumerate(keys) if k not in found]
        self.stats["cached"] += len(texts) - len(missing)
        started = time.time()
        for start in range(0, len(missing), self.batch):
            part = missing[start:start + self.batch]
            vectors = self._encoder()([texts[i] for i in part])
            fresh = {keys[i]: np.asarray(v, dtype=np.float32) for i, v in zip(part, vectors)}
            self._store(fresh)
            found.update(fresh)
            self.stats["embedded"] += len(part)
            self.log(f"  embedded {start + len(part)}/{len(missing)} ({time.time() - started:.0f}s)")
        return [found[k].tolist() for k in keys]

    def embed_query(self, query: str) -> Vector:
        """A search query, with the model's query prefix. Queries are not cached."""
        return [float(x) for x in self._encoder()([BGE_QUERY_PREFIX + query])[0]]

    # --- internals ------------------------------------------------------------

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model}\n{text}".encode("utf-8")).hexdigest()

    def _encoder(self) -> Encoder:
        if self._encode is None:
            self._encode = sentence_transformer_encoder(self.model)
        return self._encode

    @staticmethod
    def _open(path: Path) -> sqlite3.Connection:
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, vec BLOB NOT NULL)")
        return db

    def _lookup(self, keys: set[str]) -> dict[str, np.ndarray]:
        if not self._db or not keys:
            return {}
        found: dict[str, np.ndarray] = {}
        wanted = list(keys)
        for start in range(0, len(wanted), 500):               # SQLite limits the number of parameters
            part = wanted[start:start + 500]
            rows = self._db.execute(
                f"SELECT key, vec FROM vectors WHERE key IN ({','.join('?' * len(part))})", part)
            found.update({k: np.frombuffer(v, dtype=np.float32) for k, v in rows})
        return found

    def _store(self, vectors: dict[str, np.ndarray]) -> None:
        if self._db:
            self._db.executemany("INSERT OR REPLACE INTO vectors VALUES (?, ?)",
                                 [(k, v.tobytes()) for k, v in vectors.items()])
            self._db.commit()


def sentence_transformer_encoder(model: str = EMBED_MODEL) -> Encoder:
    """The real encoder: the model runs on CPU and loads once. Vectors come out normalised, so cosine = dot."""
    from sentence_transformers import SentenceTransformer

    st = SentenceTransformer(model, device="cpu")

    def encode(texts: list[str]):
        return st.encode(texts, batch_size=len(texts), normalize_embeddings=True, show_progress_bar=False)

    return encode
