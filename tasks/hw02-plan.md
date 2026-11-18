# HW02 plan: RAG slice on the real-estate corpus

Flow: `PDF / HTML -> ingest -> data/md -> chunk -> chunks.jsonl -> index (Qdrant + BM25) -> retrieve -> context -> generate -> citation check -> evals in CI`

Legend: `[ ]` todo, `[x]` done. **MANUAL** = you do it, not code. Phases run in order; later phases read what earlier ones write.

The block-1 extraction code (`src/pipeline.py`, `src/schema.py`, `prompts/v1-v4.md`, `data/golden_v4.json`, `results/`, `data/texts/`) is not touched.

---

## Decisions (settled in the grilling session)


| Area           | Decision                                                                                                                                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product        | Analyst assistant: factual Q&A about one named property or fund. "Not in the documents" when absent. No cross-document analytics.                                                                           |
| Corpus         | 30 PDFs + 10 static HTML (`data/html/`) + older editions where needed. PDFs stay committed. A PDF with an in-document Addendum/Amendment is split into logical versions via `versions:` in `doc_meta.yaml`. |
| Metadata       | Hand-written `data/doc_meta.yaml`: `title`, `doc_type`, `as_of`, `source_url` (HTML).                                                                                                                       |
| PDF to MD      | `pymupdf4llm`, then own cleanup.                                                                                                                                                                            |
| OCR            | Page with `< 50` chars and at least 1 image = `ocr_required`. Separate `ocr` command, Docling, output committed. CI never runs it.                                                                          |
| Chunking       | By heading, ~400 tokens, hard cap 480 incl. section title. Tables split between rows with header repeated. Boilerplate tagged, excluded from search.                                                        |
| Embeddings     | `BAAI/bge-small-en-v1.5` via `sentence-transformers`, cached by model + text.                                                                                                                               |
| Store          | Embedded Qdrant (local path). BM25 via `rank-bm25`.                                                                                                                                                         |
| Search configs | vector, BM25, hybrid (RRF), hybrid + rerank (`cross-encoder/ms-marco-MiniLM-L-6-v2`, top 20 -> 5).                                                                                                          |
| Answer model   | LiteLLM, `gemini/gemini-2.5-flash`. K=5, context budget 2500 tokens. Strict JSON `found/answer/citations`.                                                                                                  |
| Judge model    | `openrouter/openai/gpt-4o-mini`, `reason` before `verdict`.                                                                                                                                                 |
| Follow-ups     | Skipped. Documented in README as a future extension.                                                                                                                                                        |
| CI             | `push` + `pull_request`, path-filtered. CPU-only torch, cached model + vectors.                                                                                                                             |
| Gate           | Baseline tolerance 0.05, `false_abstain` lower-is-better, per-case regressions, plus absolute floors (set after the first run).                                                                             |
| One command    | `python main.py rag-all` and `make run`.                                                                                                                                                                    |


---



## Phase 0. MANUAL preparation (start now, in parallel with Phase 1 coding)

- [x] Save 10 public listing pages as static `.html` into `data/html/`. Pick pages with no login and a plain layout. Keep the URL and capture date for each.
- [x] Review PDFs that contain an in-document update (Addendum, Supplement, Amendment, Errata, "amended and restated"). Candidate marker lines were found in `connave` (5), `Equiton` (3), `VIOCITY`, `LMIC`, `AIE` (1 each); you found one that really updates earlier text. For each real one, note: file, page or heading where the update starts, the date of the original, the date of the update, and what it replaces. These become logical versions (see Phase 2 split).
- [x] First real version pair found: `OAM-European-Value-Fund-Offering-Memorandum-2020-12-31---Addendum-2021-12-23.pdf` (68 pages). Original OM updated 31 Dec 2020 = pages 1-65 (physical pages; 61-65 are the subscription form with roman numerals). Addendum dated 23 Dec 2021 = pages 66-68, replaces Investment Advisor address, Registered/Principal Office, redemption instructions paragraph, report-to-shareholders paragraph, documents-available paragraph, "Law" -> "Act". `doc_type: fund_om`. See `versions:` snippet in the Phase 0 section below.
- [x] Downloading older editions: you need at least 3 outdated-version trap questions. Each in-document update counts as one version pair. Download real older fund editions (earlier-year Equiton, Centurion, or AIE OM) only for what is still missing. Put them in `data/pdfs/`. Note the real edition date of each. Do not edit a PDF to fake a version.
- [x] Check the LMIC PDF: file name says Oct 28 2025 but first page regex found Aug 15 2025. Decide the right `as_of`.
- [x] Fill `data/doc_meta.yaml` with one entry per raw file, about 41 (31 PDFs + 10 HTML). Key is `file: pdfs/<name>.pdf` or `file: html/<name>.html`, relative to `data/`. Fields: `title`, `doc_type` = `listing` / `single_asset_om` / `fund_om` / `other`, `as_of`, and `source_url` (required for HTML, optional for PDF). Ingest fails if a file has no entry or an entry matches no file. Ingest will propose dates; you confirm.
- [x] For each PDF with an in-document update, add a `versions:` list in `doc_meta.yaml`. One entry per logical version: `suffix` (`original`, `addendum-1`), `start` (page or heading where it begins), `as_of`, and for updates `replaces` (the section or topic it supersedes, free text). Anything without a `versions:` list is one version.
  Example for the OAM file:
  ```yaml
  - file: pdfs/OAM-European-Value-Fund-Offering-Memorandum-2020-12-31---Addendum-2021-12-23.pdf
    title: OAM European Value Fund Offering Memorandum
    doc_type: fund_om
    versions:
      - suffix: original
        start: 1          # physical page
        as_of: 2020-12-31
      - suffix: addendum-1
        start: 66
        as_of: 2021-12-23
        replaces: investment advisor address; registered and principal office; redemption instructions paragraph; report to shareholders paragraph; documents available for inspection paragraph
  ```
  Ingest check for this file: the original ends at page 65 and the addendum starts at page 66, both Markdown files exist, and the addendum chunks still say "OAM European Value Fund" (the addendum body only says "the Fund", so the chunk header must carry the title).
- [x] Add a Gemini key and an OpenRouter key to local `.env` (already in `.env.example`).
- [x] Optional: `pip install -r requirements-ocr.txt` locally once Docling is wired (Phase 3).

Exit check: `data/html/` has 10 files, `doc_meta.yaml` has one entry per file, every PDF with an in-document update has a `versions:` list, and you can name at least 3 version pairs for the trap questions (in-document or downloaded).

---



## Phase 1. Scaffolding

- [x] Create `src/rag/` (`__init__.py`) and `src/rag_eval/` (`__init__.py`).
- [x] Add `src/rag/config.py`: paths (`data/md`, `data/ocr`, `data/chunks.jsonl`, `data/manifest.json`, `data/audit.jsonl`, `index/`), constants (`MIN_CHARS_PER_PAGE=50`, `CHUNK_TOKENS=400`, `CHUNK_MAX_TOKENS=480`, `NEAR_DUP_JACCARD=0.8`, `K=5`, `CANDIDATES=20`, `RRF_K=60`, `CONTEXT_BUDGET=2500`, `PIPELINE_VERSION`), model names read from `.env` with defaults.
- [x] Extend `requirements.txt`: `pymupdf4llm`, `beautifulsoup4`, `sentence-transformers`, `qdrant-client`, `rank-bm25`, `charset-normalizer`.
- [x] Add `requirements-ocr.txt` (Docling only).
- [x] Extend `.env.example`: `RAG_MODEL`, `JUDGE_MODEL`, `EMBED_MODEL`, `RERANK_MODEL`, matching keys.
- [x] Add `.gitignore` entries: `index/`, `.cache/`, `output/`.
- [x] Add empty subcommand stubs to `main.py`: `ingest`, `ocr`, `chunk`, `index`, `search`, `ask`, `eval-retrieval`, `rag-eval`, `rag-all`. The RAG answer eval is `rag-eval` because `eval` already scores block-1 extraction runs. Each stub prints which phase implements it and exits with code 2.
- [x] Update the root `README.md`: add a "RAG pipeline" section with the status (Phase 1 done, commands are stubs), the new setup steps (extra dependencies, `.env` variables, optional OCR requirements), a command table that marks every command as not implemented yet, and the planned folder layout. Rewrite it as each phase lands; Phase 9 finishes it.
- [x] Install the new dependencies in your venv: `pip install -r requirements.txt` (large: it pulls in PyTorch). Not needed for `--help`; first needed in Phase 2 (`pymupdf4llm`) and Phase 5 (`sentence-transformers`).

Exit check: `python main.py --help` lists the new commands, old commands still work, each stub exits with a clear message, `import src.rag.config` works.

---



## Phase 2. Ingest to Markdown

Files (few, deep modules; each has one small public function):


| File                   | Public API                                                                  | Hides                                                                                                   |
| ---------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `src/rag/meta.py`      | `load_catalog()`                                                            | YAML parsing, validation of every field, orphan and duplicate checks; reports all problems in one error |
| `src/rag/extract.py`   | `extract_pdf(path)`, `extract_html(path)`, `default_extractors()`           | layout-aware PDF to Markdown, scanned-page detection, HTML cleanup, view-source unwrap                  |
| `src/rag/normalize.py` | `normalize_pages(pages)`                                                    | NFKC, invisible chars, headers/footers, page numbers, hyphenation                                       |
| `src/rag/versions.py`  | `split_versions(entry, pages)`, `find_version_markers(pages)`               | page/heading version splits, addendum suggestions                                                       |
| `src/rag/dedup.py`     | `find_duplicates(docs)`                                                     | content hash, shingles, Jaccard, version-group exemption                                                |
| `src/rag/store.py`     | `write_markdown`, `read_markdown`, `load_ocr_pages`, cache and JSON helpers | on-disk formats (later phases read documents only through this)                                         |
| `src/rag/ingest.py`    | `ingest(...)`                                                               | orchestration, extraction cache, parallelism, manifest, audit log                                       |


Design rules applied: extractors and paths are injected (`extractors=`, `IngestPaths`), so a new format is one function plus one registry entry and tests run with fake extractors and a temp folder; only the slow step (extraction) is cached, everything else is recomputed every run so output depends only on inputs and code.

- [x] `meta.py`: load `doc_meta.yaml`, fail loudly on missing/orphan files, bad `doc_type`, bad `as_of`, missing `source_url` for HTML. Parses `versions:`.
- [x] `versions.py`: split by `versions:` start (page number or heading). Marker detection only proposes (`version_marker` events in `audit.jsonl`), never applies.
- [x] One Markdown file per logical version, `data/md/<doc_id>@<suffix>.md`, own `as_of`, `version_of` and `replaces` in front matter; page numbers stay relative to the original PDF.
- [x] Dedup runs per logical version; versions of one file are never merged.
- [x] `extract_pdf`: `pymupdf4llm` layout engine per page, built-in OCR off, pages kept separate.
- [x] A page with `< MIN_CHARS_PER_PAGE` chars and at least 1 image is `ocr_required`; without an image it is `blank`. Both go to `audit.jsonl` and the manifest.
- [x] `extract_html`: keeps `main` (fallback `body`), drops scripts, nav, footer, aside, forms and hidden elements; headings, lists and tables become Markdown; optional Chrome view-source unwrap.
- [x] `normalize_pages`: see table above. Table rows are never treated as repeated headers.
- [x] Hashes: `raw_hash` (file bytes, extraction cache key) and `content_hash` (normalized text, duplicates and `dataset_version`).
- [x] `ingest`: front matter (`doc_id`, `title`, `source`, `doc_type`, `as_of`, `source_url`, `version_of`, `replaces`, `pages`, `ocr_pages`, `content_hash`). Merges `data/ocr/<doc_id>/page-<n>.md` into the right page.
- [x] `data/manifest.json` (per file: raw hash, status, pages, `ocr_required_pages`, `blank_pages`, docs; per doc: chars, hash; `duplicates`; `dataset_version`) and an audit log `data/audit/audit-<UTC timestamp>.jsonl` (one new file per run). When a run changes the manifest, the previous `data/manifest.json` is moved to `data/manifests/manifest-<extract_version>-<hash>.json`.
- [x] Incremental: a second run skips extraction for unchanged files (`--full` forces it). One broken file is recorded as `error`, the batch continues and the command exits 1.
- [x] Tests: `tests/rag/` (17 tests, no models or real PDFs). Run `python -m pytest`.
- [x] Run `python main.py ingest` on the real corpus and check the numbers below.
- [x] Spot-check 4 files by eye: `gs01` (offering summary table), `gs9` (scrambled lease grid), one mid-size OM, a slice of Centurion. Note what `pymupdf4llm` gets wrong.

Exit check: `python main.py ingest` writes one `.md` per kept document, the newest audit file lists `ocr_required` pages and dedup decisions, a second run skips extraction. `ocr` (Phase 3) reads `ocr_required_pages` from the manifest.

## Phase 3. OCR fallback (separate command)

Files: `src/rag/ocr.py`, `requirements-ocr.txt`.

- [x] `python main.py ocr [--only TEXT...] [--limit N]`: read `data/manifest.json`, find `ocr_required_pages`, run Docling (CPU, full-page OCR, one page at a time) on those pages only, write `data/ocr/<doc_id>/page-<n>.md` as each page finishes, so an interrupted run resumes.
- [x] Skip pages that already have an OCR file. An empty file means "OCR found nothing": the page is resolved and becomes `blank` on the next ingest.
- [x] Mark OCR text so chunks later get `ocr: true`: the front matter lists `ocr_pages` per document (the chunker reads it in Phase 4).
- [x] Re-run `ingest` and confirm OCR pages are merged in page order. Result: 0 pages need OCR, `dataset_version` changed to `5c24822b709a`.
- [x] Commit `data/ocr/`. Ingest must work without Docling installed: `ocr.py` is not imported by `ingest`, and the engine is injected (`OcrEngine`), so the 3 OCR tests use a fake one.
- [x] Real run on the corpus: 124 pages OCRed in about 34 minutes on CPU, 4 found no text (`gs06` page 10, Topaz pages 7, 9, 38).
- [x] Spot-check a few OCR pages by eye (the financial statements of RESCO, BGMFll and LMIC) and note what Docling gets wrong. Known so far: a stray `$` glued to a number in one BGMFll cell.

Exit check: with Docling installed, `ocr` then `ingest` fills the previously missing pages. Without Docling, `ingest` still runs and just reports the OCR pages as pending.

---



## Phase 4. Chunking

Files: `src/rag/chunk.py`, `src/rag/tokens.py`. The fixed-window baseline and the comparison live in `measurements/chunking/`, outside the pipeline.

- [x] `chunk.py`: parse each `data/md/*.md` (front matter, headings, blocks: paragraph, list, table; page markers set the page).
- [x] Decided 2026-11-12: token counts use the embedding model's own tokenizer (`BAAI/bge-small-en-v1.5`), not `cl100k_base`, because `cl100k_base` undercounts number-heavy tables and the model silently drops everything past 512 tokens. One embedding model in the whole app. `tiktoken` is used only for the answer-model context budget in Phase 6. The tokenizer sits behind `tokens.py` (`count_tokens`, `token_spans`).
- [x] Chunk by heading: pack whole blocks up to ~400 tokens, `section` = heading path. Sibling sections never merge; a chunk under 80 tokens keeps only its own child subsection.
- [x] Decided 2026-11-12: with no heading, `section` = `<title> > page <n>`, the embedded text uses the title only, and `section_source` is `heading` or `page` (30 of 5,243 chunks use the page fallback).
- [x] Never cut a paragraph unless it is over the cap: then it splits between sentences (and between words only for a single huge sentence). A table over the limit splits between rows and repeats the header row; a row that is itself too big (a paragraph stuck in one cell) becomes several complete rows with the label cells repeated. Hard cap 480 tokens including the title and section: max in the corpus is 480, none over.
- [x] Tag `kind: boilerplate`: the chunk's own heading contains "disclaimer", "confidentiality", "table of contents" or "non-endorsement", or its text starts with a known legal phrase. Boilerplate headings never become the parent of later headings (the converter's heading levels are unreliable). 61 chunks are tagged.
- [x] Chunk fields: `chunk_id` (`<doc_id>#<index>`), `doc_id`, `source`, `title`, `section`, `section_source`, `embed_prefix`, `doc_type`, `as_of`, `version_of`, `replaces`, `doc_hash` (the document's `content_hash`), `page_start`, `page_end`, `kind`, `ocr`, `n_tokens`, `text`, `pipeline_version`. `embed_prefix` is the string to put before the text when embedding (title + heading path, or the title alone when there is no heading), so Phase 5 does not rebuild it.
- [x] `python main.py chunk` writes `data/chunks.jsonl` (5,243 chunks, 42 documents) and `data/chunks_manifest.json`. Exits 1 if any chunk is over the cap.
- [x] `measurements/chunking/fixed.py`: fixed 400/80 window, used only for the comparison.
- [x] `python main.py chunk-compare` (`measurements/chunking/compare.py`, documents in `targets.yaml`) on `gs01`, `gs9`, `Retreat at Arcway` and the first 40 pages of Centurion. Table pasted into the README.
- [x] Chunk counts are written to `data/chunks_manifest.json`, not into `data/manifest.json`: the ingest manifest stays owned by `ingest`, and `chunk` must not change what `ingest` would archive.
- [x] Side fixes found by the first full run: `normalize` now removes table-of-contents dot leaders (each dot costs a token) and shortens padded table separator rows (`|-----|` to `|---|`). Both changed `data/md/` and `dataset_version`.
- [x] Spot-check 10 random chunks by eye (a table split across chunks, an OCR chunk, an OAM addendum chunk) and note what is wrong. Known limitation: a short title-like line directly before a real heading can end a chunk (for example "Location and Market Overview").

Exit check: `python main.py chunk` writes `chunks.jsonl`, no chunk over 480 tokens, no table row cut, comparison table exists.

---



## Phase 5. Index and retrieval

Files: `src/rag/embed.py`, `src/rag/index.py`, `src/rag/bm25.py`, `src/rag/retrieve.py`, `src/rag/rerank.py`.

- [x] `embed.py`: load `bge-small-en-v1.5` once, apply the model card's query prefix, cache vectors by `EMBED_MODEL + "\n" + text`.
- [x] Embedded string = section path + chunk text. Stored payload text stays clean.
- [x] `index.py`: build Qdrant (local path, cosine), one point per chunk, payload = whole chunk. Rebuild from `chunks.jsonl` only.
- [x] `bm25.py`: tokenizer that keeps `$1,250,000`, `80231`, `9850` whole. Same string as the embedding input.
- [x] `retrieve.py`: vector top 20 + BM25 top 20, both with filters (`doc_type`, `as_of`, exclude `kind=boilerplate` by default), fuse with RRF `1/(60+rank)`, return top K.
- [x] `rerank.py`: cross-encoder over the top 20 hybrid hits, keep 5.
- [x] Unit checks without models: RRF example (`[A,B,C]` and `[C,D]` gives `C` then `A`), filter test (boilerplate and wrong `doc_type` never returned).
- [x] `python main.py search "<query>" --config vector|bm25|hybrid|rerank` prints top hits.

Exit check: `index` builds from `chunks.jsonl`, `search` returns sensible hits in all four configs, filter tests pass.

---



## Phase 6. RAG answer path

Files: `src/rag/context.py`, `src/rag/llm_rag.py`, `src/rag/answer.py`, `prompts/rag/v1/system.txt`. Prompt history is an entry in `RAG_CHANGELOG.md`.

- [x] `context.py`: greedy pack in rank order under `CONTEXT_BUDGET` (`tiktoken`), skip a block that does not fit, label `S1..Sn`, header = `source · section · as_of`. Keep `label -> chunk` map.
- [x] `llm_rag.py`: new LiteLLM call with strict JSON schema `{found, answer, citations}`, temperature 0, returns tokens, latency, cost. Does not touch `src/llm.py`.
- [x] `answer.py`: empty retrieval returns the abstain constant without a model call; call model; strip brackets, drop unknown labels, dedupe; `found` with no valid label becomes abstain; map labels to `chunk_id`, source, section.
- [x] Abstain sentence is a constant in code.
- [x] `prompts/rag/v1/system.txt`: answer only from `<sources>`, cite labels, copy numbers and addresses exactly, subject property beats comparables, later `as_of` wins and name the older figure, fund text is about the fund and listing text about the building, similar property is not an answer.
- [x] Prompt v1 recorded in `RAG_CHANGELOG.md`.
- [x] Log per question: query, retrieved ids, ids in context, cited ids, invalid labels, tokens, cost, latency. Write to `output/answers-*.jsonl`.
- [x] `python main.py ask "<question>"` prints answer plus citations.

Exit check: `ask` answers a known question with a citation, and says "not in the documents" for a made-up property.

---



## Phase 7. Test set, scoring, retrieval eval

Files: `evals/testset.json`, `evals/labels.json`, `evals/baseline.json`, `src/rag_eval/lint.py`, `score.py`, `retrieval_eval.py`, `judge.py`, `gate.py`, `run.py`, `prompts/rag/judge-v1/correct.txt`, `prompts/rag/judge-v1/grounded.txt`.

**MANUAL (after Phase 4 is stable)**

- [x] Write `evals/testset.json` by reading the Markdown and chunks. About 28 questions: 6 exact facts, 5 paraphrases, 4 similar-document traps (for example gs02 vs gs03), 3 outdated-version traps (from in-document addenda and any downloaded older editions; the expected answer is the newer value, and it should name the older one), 4 no-answer (2 missing property, 2 field never stated), 3 multi-chunk, 3 fund-vs-listing.
- [x] Each case: `id`, `kind`, `question`, `source`, `evidence` (short quote), `must` (fact groups: groups are AND, options inside are OR), `reference`, optional `doc_type` filter. No-answer cases have no `must` and no `evidence`.
- [x] Verify every expected answer yourself. AI may draft, you check.
- [x] Review Appendix A: 29 proposed questions, mark each `keep`, `edit`, or `drop`, fill the 3 `TBD` rows, and add `evidence` and `must` for each kept row.
- [x] Outdated-version traps (candidates for the OAM file are already in Appendix A as o01-o04): once `versions:` is in `doc_meta.yaml` and the split Markdown exists, ask the assistant to propose 3 to 5 candidate questions per version pair. For each it quotes the old value and the new value from the two Markdown files with page numbers. You accept, edit, or drop each one. Use these templates:
  - Current value: "What is  for <fund/property>?" Expected: the newer value, and the answer names the older one.
  - Direct comparison: "Did  change between the original and the addendum?" Expected: states both values.
  - Old-only trap: "What was  in the original ?" Expected: the older value, citing the original version. This checks that the newer-wins rule does not erase history.
  - Unaffected neighbor: a question about a field the update did not touch. Expected: unchanged value, no mention of the update.

**Code**

- [x] `lint.py`: `evidence` found in exactly the expected document, each `must` string present in the evidence chunks, no-answer cases have no `must`/`evidence`, duplicate ids, each `kind` has at least 2 cases. Resolve evidence to current chunk ids at run time. `python main.py lint-testset`.
- [x] `retrieval_eval.py`: recall@5, MRR, ms/query, missed ids, for vector / bm25 / hybrid / hybrid+rerank on answerable cases. Fake-data unit test: ranks 2, 1, missing gives recall 0.67 and MRR 0.50.
- [x] `score.py`: deterministic `facts`, `cited` (a resolved relevant chunk is among citations), `abstain`, `pass`. Numbers within 1%, strings normalized. Inapplicable scores are `None`.
- [x] `judge.py`: `reason` then `verdict`, uses `JUDGE_MODEL`, reference in the prompt. Groundedness: claim-level check against cited chunk text, abstain returns no claims.
- [x] `gate.py`: baseline tolerance 0.05, `false_abstain` lower-is-better, per-case regression list, absolute floors (initial: `recall@5 >= 0.8`, `pass >= 0.7`, `abstain = 1.0`, `grounded >= 0.85`; tune later). Exit 1 on failure.
- [x] `run.py`: run all cases, `--repeat N`, aggregate by kind, write `output/report-<prompt>-<timestamp>.md` and `eval-*.json`. `python main.py rag-eval`.
- [x] Write cost per 1000 questions from measured tokens.

**MANUAL (after the first full run)**

- [x] Hand-label 15 of the bot's real answers (`correct`, `grounded`, one-line note). At least 5 must be wrong answers. Save as `evals/labels.json`.

**Code**

- [x] `calibrate`: run the judge on the 15, print agreement, false pass, false fail, disagreement ids. `python main.py calibrate`. Agreement was not low enough to write `judge-v2` (correct 0.93, grounded 0.86, false_pass 0.00 on both).
- [x] Build `evals/baseline.json` from 3 repeated runs, record flaky cases. `python main.py save-baseline`. From `eval-v2-20261117T110607Z.json`: 19 passed every time; flaky e02, o02, n04, f02.
- [x] k-sweep (3, 5, 10): quality, tokens, cost. Table is in `RAG_REPORT.md`. `python main.py k-sweep`. Recall 0.89 / 0.96 / 1.00, pass 0.83 / 0.72 / 0.83, answer cost per 1000 $1.20 / $1.63 / $2.29. Default k stays 5.
- [x] Set real floor values from the first run and commit.

**Exit check**

- [x] Lint passes. `python main.py lint-testset`: 29 cases, 0 errors.
- [x] Retrieval table has four configs (`vector`, `bm25`, `hybrid`, `rerank`): recall@5, MRR, ms/query, missed ids. Printed under `## Retrieval` by `python main.py rag-eval`.
- [x] Answer metrics are printed: recall@5, pass, facts, cited, abstain, false abstain, judge, grounded, cost per 1000.
- [x] Calibration is printed. `python main.py calibrate`: correct agreement 0.93, grounded agreement 0.86, false pass 0.00 on both.
- [x] The gate passes on the shipped prompt against `evals/baseline.json`. Prompt v5 (`report-v5-20261117T220624Z`) passed. Floors stay recall@5 0.80, pass 0.70, abstain 1.00, grounded 0.85.
- [x] The gate fails on a worse prompt. v3 (`report-v3-20261117T155837Z`) exited 1: facts 0.76 fell below 0.81, regression s04. v4 exited 1 on regression s04. The shipped prompt is v5.

---



## Phase 8. CI

Files: `.github/workflows/evals.yml`, `Makefile`.

- [ ] Workflow trigger: `push` and `pull_request`, paths `prompts/rag/**`, `evals/**`, `src/rag/**`, `src/rag_eval/**`, `data/chunks.jsonl`, `requirements.txt`.
- [ ] Python 3.12, CPU-only torch (`--index-url https://download.pytorch.org/whl/cpu`), `pip install -r requirements.txt`.
- [ ] `actions/cache` for the Hugging Face model folder and the vector cache (key: hash of `chunks.jsonl` + embed model).
- [ ] Steps in order: offline unit checks, test-set lint, index build, retrieval metrics, answer eval + judge + gate.
- [ ] **MANUAL** before the first CI run: add `GEMINI_API_KEY` and `OPENROUTER_API_KEY` as GitHub repo secrets (Settings -> Secrets and variables -> Actions). The workflow reads both; without them the answer and judge steps fail.
- [ ] Upload `output/report-*.md` with `if: always()`. Timeout 20 minutes.
- [ ] `Makefile`: `run` calls `python main.py rag-all`.
- [ ] `python main.py rag-all`: ingest, chunk, index, retrieval eval, answer eval, print report table. Skips `ocr`, skips unchanged inputs.
- [ ] Push a branch and confirm the workflow passes. Then make a worse prompt change and confirm it fails.

Exit check: a green run on the baseline and a red run on a worse prompt, both visible in GitHub Actions.

---



## Phase 9. Report and README

- [ ] `README.md`: new RAG section with setup, commands, project layout, one-command run, cost per 1000 questions, chunking rationale and the fixed-window comparison table, known limits (photo-only pages, over-detected tables), follow-up rewrite listed as a future extension.
- [ ] `REPORT.md`: add a RAG section. Retrieval table (four configs), answer metrics, judge calibration, 3 to 5 failures (expected, actual, stage, why), what you would change next. The k-sweep table is in `RAG_REPORT.md`. Leave the extraction report as it is.
- [ ] `.env.example` updated, no secrets committed, `index/` and `output/` ignored.
- [ ] Final check against the homework list: code, `data/` + manifest, `prompts/` with changelog, `evals/`, `.github/workflows/`, `REPORT.md`, `README.md`.
- [ ] Repo is public and the link is ready.

---



## Appendix A. Proposed test questions (review in Phase 7)

How to use: go through the table, mark each row `keep`, `edit`, or `drop`, and fill the `TBD` rows. For every kept row, open the Markdown and copy a short `evidence` quote that is really there. Expected values below come from `data/golden_v4.json` (your hand labels), from text I read in the PDFs, or are marked `TBD`. None of them has been checked against the new Markdown yet, so each one needs a check against the Markdown or the PDF before it goes into `evals/testset.json`.

Status key: **golden** = taken from `golden_v4.json`, verify in Markdown. **seen** = I read it in the extracted text. **TBD** = pick after reading the corpus.

Target mix: 6 exact, 5 paraphrase, 4 similar-document, 4 outdated-version, 4 no-answer, 3 multi-chunk, 3 fund-vs-listing (29 rows, about 20 answerable plus 4 no-answer plus traps; drop weak ones to land near 28).


| ID  | Kind             | Question                                                                                                        | Expected answer                                                                                                                                                          | Source                  | Status                                                                                                                                                                   |
| --- | ---------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| e01 | exact            | What is the land list price for 9850 East Girard Avenue?                                                        | $1,250,000                                                                                                                                                               | gs01                    | seen                                                                                                                                                                     |
| e02 | exact            | What is the lot size of the 33-unit Denver development?                                                         | 0.78 acres (34,076 SF)                                                                                                                                                   | gs01                    | seen                                                                                                                                                                     |
| e03 | exact            | What is the monthly lease rate at 16213 Illinois Ave?                                                           | $7,937 per month                                                                                                                                                         | gs9                     | golden. This PDF's lease table is scrambled, so it tests extraction too                                                                                                  |
| e04 | exact            | What is the asking price of 1028 Johnson Street, Kingston?                                                      | $1,189,900                                                                                                                                                               | 1028 Johnson            | seen                                                                                                                                                                     |
| e05 | exact            | What is the asking price of 849 North Bunker Hill Avenue?                                                       | $16,995,000                                                                                                                                                              | gs03                    | golden                                                                                                                                                                   |
| e06 | exact            | What asset management fee does Centurion REIT's Asset Manager receive?                                          | 1.00% per annum, plus HST                                                                                                                                                | Centurion OM            | seen. Check the surrounding text for what the fee is based on                                                                                                            |
| p01 | paraphrase       | How much is the seller asking for the Denver land planned for 33 apartments?                                    | $1,250,000                                                                                                                                                               | gs01                    | seen                                                                                                                                                                     |
| p02 | paraphrase       | How tall, in floors, is the building at 8000 Wisconsin Avenue?                                                  | 20 floors                                                                                                                                                                | gs06                    | golden                                                                                                                                                                   |
| p03 | paraphrase       | What would it cost per month to rent the fenced contractor's yard and shop in Paramount?                        | $7,937 per month                                                                                                                                                         | gs9                     | golden                                                                                                                                                                   |
| p04 | paraphrase       | Where is the 14-unit building on Meridian Street located?                                                       | Los Angeles, CA 90042                                                                                                                                                    | gs04                    | golden                                                                                                                                                                   |
| p05 | paraphrase       | What does a buyer pay per apartment at 849 N Bunker Hill?                                                       | $459,324 per unit                                                                                                                                                        | gs03                    | golden                                                                                                                                                                   |
| s01 | similar-doc      | How many units does 708-712 New Depot Street have?                                                              | 33 units (not 37, which is 849 N Bunker Hill)                                                                                                                            | gs02                    | golden                                                                                                                                                                   |
| s02 | similar-doc      | What is the asking price of 708-712 New Depot Street?                                                           | $6,450,000 (not $16,995,000)                                                                                                                                             | gs02                    | golden                                                                                                                                                                   |
| s03 | similar-doc      | How many floors does 849 North Bunker Hill have?                                                                | 12 floors (not 6, which is New Depot)                                                                                                                                    | gs03                    | golden                                                                                                                                                                   |
| s04 | similar-doc      | What is the condition of 5623 Meridian Street?                                                                  | Needs renovation                                                                                                                                                         | gs04                    | golden. Other LA brochures from the same broker are close in wording                                                                                                     |
| o01 | outdated-version | Where does a shareholder send redemption instructions for the OAM European Value Fund?                          | Principal office (addendum p.67), replacing "registered office" (original p.19); answer names the old value                                                              | OAM original + addendum | seen                                                                                                                                                                     |
| o02 | outdated-version | What is the Investment Advisor's address for the OAM European Value Fund?                                       | c/o Campbells Corporate Services Limited, Floor 4, Willow House, Cricket Square, KY1-9010 (addendum p.66); replaces The Pavilion, Cricket Square, P.O. Box 597, KY1-1107 | OAM original + addendum | seen                                                                                                                                                                     |
| o03 | outdated-version | What was the Investment Advisor's address in the December 2020 OAM offering memorandum?                         | The Pavilion, Cricket Square, P.O. Box 597, Grand Cayman KY1-1107 (cover page); must cite the original, not the addendum                                                 | OAM original            | seen                                                                                                                                                                     |
| o04 | outdated-version | What is the cut-off time for OAM redemption requests?                                                           | 3:30 p.m. Cayman time, 14 days before the Redemption Day. Unchanged by the addendum, so the answer should not mention it                                                 | OAM original            | seen. Unaffected-neighbor check                                                                                                                                          |
| n01 | no-answer        | What is the asking price of 8000 Wisconsin Avenue?                                                              | Not stated (golden has `amount: null`)                                                                                                                                   | gs06                    | golden. Confirm the document really gives no price                                                                                                                       |
| n02 | no-answer        | What is the asking price of a named property that is not in the corpus?                                         | Not in the documents                                                                                                                                                     | none                    | TBD. Pick an address outside the corpus and check no document contains it                                                                                                |
| n03 | no-answer        | A field a listing never states, for a property that is in the corpus (for example property taxes or year built) | Not in the documents                                                                                                                                                     | one listing             | TBD. Search the Markdown first to confirm the field is absent                                                                                                            |
| n04 | no-answer        | A fund fact the OM never states (for example a fee type the OM does not mention)                                | Not in the documents                                                                                                                                                     | one fund OM             | TBD. Search the OM for the word first                                                                                                                                    |
| m01 | multi-chunk      | For the Denver 33-unit project, what is the list price and the parking ratio?                                   | $1,250,000 and 1.25/1,000 SF                                                                                                                                             | gs01                    | seen. Check that the two facts land in different chunks; if not, replace with a pair from different sections                                                             |
| m02 | multi-chunk      | For 849 N Bunker Hill, what is the asking price and what amenities does it list?                                | $16,995,000 plus amenities such as elevator, fitness center, rooftop lounge, EV chargers                                                                                 | gs03                    | golden                                                                                                                                                                   |
| m03 | multi-chunk      | What did the 23 December 2021 OAM addendum change?                                                              | Advisor address, registered and principal office, redemption instructions, report-to-shareholders paragraph, documents-available paragraph, "Law" to "Act"               | OAM addendum            | seen. The expected list is long, so score by `must` fact groups, not by full match                                                                                       |
| f01 | fund-vs-listing  | What is the minimum initial subscription for the OAM European Value Fund?                                       | US$250,000 per investor                                                                                                                                                  | OAM original            | seen. Use `doc_type=fund_om`                                                                                                                                             |
| f02 | fund-vs-listing  | Who is the investment advisor of the OAM European Value Fund?                                                   | Overseas Asset Management (Cayman) Ltd.                                                                                                                                  | OAM original            | seen                                                                                                                                                                     |
| f03 | fund-vs-listing  | What is the zoning for the Denver 33-unit project?                                                              | B3, Denver County                                                                                                                                                        | gs01                    | seen. Filter to `doc_type` in (`listing`, `single_asset_om`) so no fund OM can answer. gs01 is a `single_asset_om`, so a bare `doc_type=listing` filter would exclude it |




Known data issue to settle before using gs05 questions: the golden file says `6535 OASIS AVENUE` but the PDF file name says `6563 OASIS AVENUE`. Check the PDF and fix whichever is wrong before writing any question about that listing. (None of the questions above uses gs05 yet.)

Checks before a row is final:

- [ ] Every `evidence` quote is found in exactly the expected document (lint will enforce this).
- [ ] Every `must` string actually appears in the evidence chunks.
- [ ] No-answer rows: grep the Markdown for the missing fact and confirm it is not there.
- [ ] Outdated-version rows: the expected answer names both values and cites the right version.
- [ ] You wrote or reviewed every expected answer yourself; none is copied from an unreviewed AI draft.

---



## Order at a glance


| #   | Phase             | Needs from before                      | You                                                  |
| --- | ----------------- | -------------------------------------- | ---------------------------------------------------- |
| 0   | Manual prep       | none                                   | HTML, older editions, `doc_meta.yaml`, keys, secrets |
| 1   | Scaffolding       | none                                   |                                                      |
| 2   | Ingest            | 0, 1                                   | spot-check 4 files                                   |
| 3   | OCR               | 2                                      | run once with Docling                                |
| 4   | Chunking          | 2 (and 3 if OCR is wanted)             | review comparison table                              |
| 5   | Index + retrieval | 4                                      |                                                      |
| 6   | RAG answer        | 5                                      |                                                      |
| 7   | Test set + evals  | 4 for writing questions, 6 for answers | write 28 questions, label 15 answers                 |
| 8   | CI                | 7                                      | add secrets                                          |
| 9   | Report + README   | all                                    |                                                      |


Open items to settle later (not blocking): exact gate floors, `judge-v2` wording after calibration, whether to keep `pymupdf4llm` for a file where it fails (custom fix), repo size check if PDFs push it past ~250 MB.