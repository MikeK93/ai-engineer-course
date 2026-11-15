"""Paths, constants and model names for the RAG pipeline.

Block-1 extraction code keeps using src/config.py. This module only adds what the RAG
pipeline needs and reuses ROOT, DATA, PDFS and PROMPTS from there.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from ..config import DATA, PDFS, PROMPTS, ROOT

load_dotenv(ROOT / ".env")

# --- inputs -----------------------------------------------------------------
PDF_DIR = PDFS                        # data/pdfs
HTML_DIR = DATA / "html"
DOC_META = DATA / "doc_meta.yaml"     # one entry per raw file, key is pdfs/<name> or html/<name>

# --- ingest / chunk outputs -------------------------------------------------
MD_DIR = DATA / "md"                  # one Markdown file per logical document version
OCR_DIR = DATA / "ocr"                # data/ocr/<doc_id>/page-<n>.md, written by `ocr`
CHUNKS = DATA / "chunks.jsonl"
MANIFEST = DATA / "manifest.json"
MANIFEST_DIR = DATA / "manifests"        # one snapshot per extract version: manifest-<extract_version>.json
AUDIT_DIR = DATA / "audit"               # one file per ingest run: audit-<UTC timestamp>.jsonl

# --- index, caches, outputs (not committed) ---------------------------------
INDEX_DIR = ROOT / "index"            # embedded Qdrant
CACHE_DIR = ROOT / ".cache"           # embedding cache
OUTPUT_DIR = ROOT / "output"          # answer logs, eval reports

# --- prompts and evals (committed) ------------------------------------------
RAG_PROMPTS = PROMPTS / "rag"         # prompts/rag/v1/system.txt, judge-v1/...
EVALS_DIR = ROOT / "evals"            # testset.json, labels.json, baseline.json

# --- pipeline constants -----------------------------------------------------
PIPELINE_VERSION = "rag-v2"           # bump when ingest or chunk behavior changes
EXTRACT_VERSION = "extract-v2"        # bump when an extractor changes: invalidates the extraction cache
EXTRACT_CACHE = CACHE_DIR / "ingest"  # extracted pages, keyed by file hash + EXTRACT_VERSION

MIN_CHARS_PER_PAGE = 50               # a page below this needs an image or drawings to be `ocr_required`
MIN_DRAWINGS_FOR_OCR = 20             # text drawn as vector outlines has no text layer and no image
NEAR_DUP_JACCARD = 0.8                # word 5-shingles
SHINGLE_WORDS = 5

CHUNK_TOKENS = 400                    # target size, counted with the embedding model's tokenizer
CHUNK_MAX_TOKENS = 480                # hard cap including the section path (embedding model reads 512)
CHUNK_MIN_TOKENS = 80                 # a new heading only starts a new chunk once the current one has this many
CHUNK_TINY_TOKENS = 50                # a chunk with fewer text tokens is squashed into a neighbour
CHUNK_MODEL_MAX_TOKENS = 512          # what the embedding model can read: a single sentence may use the room above the cap
MIN_WORDS_PER_CHUNK = 3               # a chunk of one or two words (and no digit) looks like a title and is dropped
# Chunks whose own heading (or first line) matches this are tagged `skip_candidate`: sale / rent comparables
# describe other properties and would answer questions about the wrong one.
COMPARABLES_PATTERN = r"\bcomparables?\b|\bcomps\b"
GARBLED_SHARE = 0.3                   # a page where this share of characters is private-use glyphs is unreadable (symbol font)
# A chunk is tagged `boilerplate` (kept, but excluded from search) when its section path contains one of
# these words, or its text starts with one of these legal phrases.
BOILERPLATE_HEADINGS = ("disclaimer", "confidentiality", "table of contents", "non-endorsement")
BOILERPLATE_PHRASES = (
    "this information supplied herein is from sources we deem reliable",
    "the information contained in the following marketing brochure is proprietary and strictly confidential",
    "marcus & millichap is not affiliated with, sponsored by, or endorsed by",
)

COLLECTION = "chunks"                 # Qdrant collection name
EMBEDDING_CACHE = CACHE_DIR / "embeddings.sqlite"   # vectors keyed by model + text
# bge models embed a search query with this prefix; passages are embedded as they are.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

K = 5                                 # chunks sent to the model
CANDIDATES = 20                       # per search before fusion, and into the reranker
RRF_K = 60
CONTEXT_BUDGET = 2500                 # tokens of sources in the prompt

@dataclass(frozen=True)
class IngestPaths:
    """Every location `ingest` reads or writes. Tests pass a temp folder instead of the defaults."""

    data: Path = DATA
    doc_meta: Path = DOC_META
    md: Path = MD_DIR
    ocr: Path = OCR_DIR
    manifest: Path = MANIFEST          # always the latest run
    manifest_dir: Path = MANIFEST_DIR
    audit_dir: Path = AUDIT_DIR
    cache: Path = EXTRACT_CACHE


@dataclass(frozen=True)
class ChunkPaths:
    """Every location `chunk` reads or writes."""

    md: Path = MD_DIR
    manifest: Path = MANIFEST            # read for dataset_version
    chunks: Path = CHUNKS
    summary: Path = DATA / "chunks_manifest.json"   # always the latest run
    summary_dir: Path = MANIFEST_DIR                # previous run, moved: chunks-manifest-<pipeline_version>-<hash>.json


@dataclass(frozen=True)
class IndexPaths:
    """Every location `index` and `search` read or write. Nothing here is committed: it is rebuilt from `chunks`."""

    chunks: Path = CHUNKS
    index: Path = INDEX_DIR              # embedded Qdrant
    embedding_cache: Path = EMBEDDING_CACHE


# --- models (override in .env) ----------------------------------------------
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
RERANK_MODEL = os.environ.get("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_MODEL = os.environ.get("RAG_MODEL", "gemini/gemini-2.5-flash")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openrouter/openai/gpt-4o-mini")
