"""Paths, constants and model names for the RAG pipeline.

Block-1 extraction code keeps using src/config.py. This module only adds what the RAG
pipeline needs and reuses ROOT, DATA, PDFS and PROMPTS from there.
"""

import os

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
AUDIT = DATA / "audit.jsonl"

# --- index, caches, outputs (not committed) ---------------------------------
INDEX_DIR = ROOT / "index"            # embedded Qdrant
CACHE_DIR = ROOT / ".cache"           # embedding cache
OUTPUT_DIR = ROOT / "output"          # answer logs, eval reports

# --- prompts and evals (committed) ------------------------------------------
RAG_PROMPTS = PROMPTS / "rag"         # prompts/rag/v1/system.txt, judge-v1/...
EVALS_DIR = ROOT / "evals"            # testset.json, labels.json, baseline.json

# --- pipeline constants -----------------------------------------------------
PIPELINE_VERSION = "rag-v1"           # bump when ingest or chunk behavior changes

MIN_CHARS_PER_PAGE = 50               # a page below this with an image is `ocr_required`
NEAR_DUP_JACCARD = 0.8                # word 5-shingles
SHINGLE_WORDS = 5

CHUNK_TOKENS = 400                    # target size, cl100k_base
CHUNK_MAX_TOKENS = 480                # hard cap including the section path (embedding model reads 512)

K = 5                                 # chunks sent to the model
CANDIDATES = 20                       # per search before fusion, and into the reranker
RRF_K = 60
CONTEXT_BUDGET = 2500                 # tokens of sources in the prompt

# --- models (override in .env) ----------------------------------------------
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
RERANK_MODEL = os.environ.get("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_MODEL = os.environ.get("RAG_MODEL", "gemini/gemini-2.5-flash")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openrouter/openai/gpt-4o-mini")
