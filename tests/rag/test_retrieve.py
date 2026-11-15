"""Index and retrieval tests. A hashing encoder and a fake scorer stand in for the models, so nothing is
downloaded; Qdrant runs in memory."""

import re
import zlib

import numpy as np

from src.rag.bm25 import Bm25Index, tokenize
from src.rag.embed import Embedder, embedding_text
from src.rag.index import Filters, as_of_num, build_index, open_client
from src.rag.rerank import Reranker
from src.rag.retrieve import Retriever, rrf_fuse

DIM = 64


def encode(texts):
    """Bag of words hashed into 64 dimensions, normalised: similar words = similar vectors."""
    out = []
    for text in texts:
        v = np.zeros(DIM, dtype=np.float32)
        for word in re.findall(r"\w+", text.lower()):
            v[zlib.crc32(word.encode()) % DIM] += 1
        out.append(v / (np.linalg.norm(v) or 1))
    return out


def chunk(i, text, *, section="Overview", doc_type="listing", as_of="2024-05-01", kind="content", skip=False):
    return {"chunk_id": f"d#{i}", "doc_id": "d", "source": "pdfs/d.pdf", "title": "Doc", "section": section,
            "embed_prefix": f"Doc | {section}", "text": text, "doc_type": doc_type, "as_of": as_of, "kind": kind,
            "skip_candidate": skip, "page_start": 1, "page_end": 1}


CHUNKS = [
    chunk(0, "The asking price is $1,250,000 for the building at 9850 East Girard Avenue, Denver, CO 80231."),
    chunk(1, "Tenants pay rent monthly and the lease runs for five years with renewal options."),
    chunk(2, "Disclaimer: this information is from sources we deem reliable.", kind="boilerplate"),
    chunk(3, "Sale comparables: 120 Main Street sold for $2,000,000 last year.", skip=True),
    chunk(4, "The fund invests in mortgages and pays a quarterly distribution.", doc_type="fund_om", as_of="2021"),
    chunk(5, "Parking: six surface spaces and a loading dock at the rear of the property."),
]


def retriever(reranker=None, chunks=CHUNKS):
    embedder = Embedder(encode, cache=None, log=lambda _: None)
    client = open_client(":memory:")
    build_index(chunks, embedder, client, log=lambda _: None)
    return Retriever(client, Bm25Index(chunks), embedder, chunks, reranker=reranker)


# --- fusion ---------------------------------------------------------------------

def test_rrf_puts_the_chunk_found_by_both_lists_first():
    fused = rrf_fuse([["A", "B", "C"], ["C", "D"]])
    assert [i for i, _ in fused] == ["C", "A", "B", "D"]
    assert abs(dict(fused)["C"] - (1 / 63 + 1 / 61)) < 1e-12


# --- BM25 keeps figures whole -----------------------------------------------------

def test_tokenizer_keeps_money_zip_and_street_number_whole():
    assert tokenize("Price $1,250,000, zip 80231, 9850 East Girard; yield 5.25%.") == [
        "price", "$1,250,000", "zip", "80231", "9850", "east", "girard", "yield", "5.25%"]


def test_bm25_finds_an_exact_figure_and_respects_the_filter():
    index = Bm25Index(CHUNKS)
    assert index.search("$1,250,000", 3)[0][0] == "d#0"
    assert index.search("$1,250,000", 3, lambda c: c["doc_type"] == "fund_om") == []     # filtered out, not just demoted
    assert index.search("zzzz nothing", 3) == []


# --- filters: boilerplate and the wrong type are never returned, by any config ----

def test_filters_default_leave_out_boilerplate_and_comparables():
    f = Filters()
    assert [c["chunk_id"] for c in CHUNKS if f.accepts(c)] == ["d#0", "d#1", "d#4", "d#5"]
    assert Filters(include_boilerplate=True, include_skip=True).accepts(CHUNKS[2])
    assert [c["chunk_id"] for c in CHUNKS if Filters(doc_types=("fund_om",)).accepts(c)] == ["d#4"]
    assert [c["chunk_id"] for c in CHUNKS if Filters(as_of_min="2022").accepts(c)] == ["d#0", "d#1", "d#5"]


def test_every_config_returns_only_allowed_chunks():
    r = retriever(reranker=Reranker(lambda pairs: [len(p) for _, p in pairs]))
    for config in ("vector", "bm25", "hybrid", "rerank"):
        ids = [h.chunk["chunk_id"] for h in r.search("sold disclaimer price", config, k=10)]
        assert "d#2" not in ids and "d#3" not in ids, config            # boilerplate and comparables
        ids = [h.chunk["chunk_id"] for h in r.search("price rent mortgages", config, filters=Filters(doc_types=("fund_om",)), k=10)]
        assert set(ids) <= {"d#4"}, config
    assert [h.chunk["chunk_id"] for h in r.search("comparables sold", "hybrid", filters=Filters(include_skip=True), k=1)] == ["d#3"]


def test_qdrant_and_python_filters_agree():
    r = retriever()
    for f in (Filters(), Filters(as_of_min="2022"), Filters(doc_types=("fund_om", "listing")), Filters(include_skip=True)):
        qdrant_ids = {h.chunk["chunk_id"] for h in r.search("property mortgage price rent", "vector", filters=f, k=10)}
        assert qdrant_ids == {c["chunk_id"] for c in CHUNKS if f.accepts(c)}


def test_as_of_num():
    assert (as_of_num("2021"), as_of_num("2021-12"), as_of_num("2021-12-23")) == (20210101, 20211201, 20211223)


# --- search configs ---------------------------------------------------------------

def test_hybrid_finds_the_exact_figure_and_records_both_ranks():
    [top, *_] = retriever().search("asking price $1,250,000", "hybrid", k=3)
    assert top.chunk["chunk_id"] == "d#0" and set(top.ranks) == {"vector", "bm25"}


def test_vector_config_uses_the_query_prefix():
    seen = []
    embedder = Embedder(lambda texts: seen.extend(texts) or encode(texts), cache=None, log=lambda _: None)
    embedder.embed_query("where is it")
    assert seen[0].startswith("Represent this sentence for searching relevant passages: ")


def test_rerank_reorders_the_hybrid_candidates_and_keeps_five():
    chunks = [chunk(i, f"property detail number {i} about parking and rent") for i in range(10)]
    first = retriever(chunks=chunks).search("parking", "hybrid", k=20)
    # the fake cross-encoder prefers higher chunk numbers, whatever the first stage thought
    r = retriever(reranker=Reranker(lambda pairs: [int(re.search(r"number (\d+)", p).group(1)) for _, p in pairs]), chunks=chunks)
    hits = r.search("parking", "rerank", k=5)
    assert [h.chunk["chunk_id"] for h in hits] == ["d#9", "d#8", "d#7", "d#6", "d#5"]
    assert hits[0].ranks["rerank"] == 1 and "vector" in hits[0].ranks and len(first) == 10


# --- embedding cache ----------------------------------------------------------------

def test_embedding_cache_is_keyed_by_model_and_text_and_skips_known_texts(tmp_path):
    calls = []

    def counting(texts):
        calls.append(list(texts))
        return encode(texts)

    db = tmp_path / "cache.sqlite"
    first = Embedder(counting, cache=db, model="m1", log=lambda _: None)
    v1 = first.embed_documents(["alpha beta", "gamma"])
    second = Embedder(counting, cache=db, model="m1", log=lambda _: None)
    v2 = second.embed_documents(["gamma", "alpha beta", "delta"])
    assert calls == [["alpha beta", "gamma"], ["delta"]]                       # only the new text is encoded
    assert v2[0] == v1[1] and v2[1] == v1[0] and second.stats == {"cached": 2, "embedded": 1}
    other_model = Embedder(counting, cache=db, model="m2", log=lambda _: None)
    other_model.embed_documents(["gamma"])
    assert calls[-1] == ["gamma"]                                              # a different model never reuses vectors


def test_embedded_string_is_the_prefix_then_the_text_and_the_payload_stays_clean():
    c = CHUNKS[0]
    assert embedding_text(c) == f"Doc | Overview\n{c['text']}"
    client = open_client(":memory:")
    build_index(CHUNKS[:2], Embedder(encode, cache=None, log=lambda _: None), client, log=lambda _: None)
    [point] = client.retrieve("chunks", ids=[0], with_payload=True)
    assert point.payload["text"] == c["text"] and point.payload["as_of_num"] == 20240501
