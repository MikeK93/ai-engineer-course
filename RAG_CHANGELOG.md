# RAG changelog

Every change to the RAG pipeline, newest first, with the reason for it. The block-1 extraction service has its own history in `REPORT.md` and `prompts/`.

Entry format:

```
## <date> | <phase> | <short title>   (commit <hash>)
What: what changed.
Why: the reason, and what was rejected.
Effect: measured result or open risk.
```

Rules: one entry per meaningful change (code, data, prompt, config, model). Record the metrics before and after when a change touches retrieval or answers. Prefer "why" over "what"; the diff already shows what.

---

## 2026-11-12 | Phase 4 | DECISION: production chunking is "by heading"

What: the pipeline's `chunk` command uses the structure-aware "by heading" strategy (`src/rag/chunk.py`). Fixed 400/80 windows are kept only as a measurement baseline, in `measurements/chunking/` (`compare.py`, `fixed.py`, `targets.yaml`), run with `python main.py chunk-compare`. The documents compared are listed in `measurements/chunking/targets.yaml`, and `chunk` does not read that file. Sizes are counted with the embedding model's own tokenizer (bge-small, 512-token limit).

Evidence (the Centurion row is its first 40 pages):

| Document | Strategy | Chunks | Avg tokens | Max tokens | Mid-sentence starts | Cut table rows | Empty section | Over 512 |
|---|---|---|---|---|---|---|---|---|
| gs01 (offering summary table) | by heading | 19 | 177 | 394 | 0 | 0 | 0 | 0 |
| gs01 | fixed 400/80 | 10 | 382 | 400 | 1 | 4 | 10 | 0 |
| gs9 (dense paragraphs) | by heading | 4 | 227 | 394 | 0 | 0 | 0 | 0 |
| gs9 | fixed 400/80 | 3 | 350 | 400 | 1 | 0 | 3 | 0 |
| Retreat at Arcway (mid-size OM) | by heading | 80 | 267 | 477 | 0 | 0 | 0 | 0 |
| Retreat at Arcway | fixed 400/80 | 61 | 398 | 400 | 23 | 35 | 61 | 0 |
| Centurion (pages 1-40) | by heading | 137 | 236 | 479 | 0 | 0 | 0 | 0 |
| Centurion (pages 1-40) | fixed 400/80 | 98 | 398 | 400 | 49 | 28 | 98 | 0 |

Why by heading:
- It never starts a chunk mid-sentence, never cuts a table row, and every chunk has a section. Fixed windows did all three wrongly: 23 mid-sentence starts and 35 cut rows on Retreat at Arcway, 49 and 28 on the Centurion slice, and no section on any chunk.
- The section is what makes a citation say where an answer came from, and `embed_prefix` (title + section) gives the embedding model context for numbers and short facts. Fixed windows have neither.
- Tables are the content the questions depend on (rent rolls, offering summaries, financial statements). Cutting a row separates a number from its label.

What it costs: chunks are smaller (average 177 to 267 tokens against about 400) and there are about 30 to 40 percent more of them, because headings end chunks early. That means more vectors and more candidates for the reranker. Both are cheap at this corpus size (5,243 chunks). The price is accepted; if retrieval recall turns out weak in Phase 7, merging adjacent small chunks is the first thing to try, not a return to fixed windows.

Limits of the evidence: 4 documents, no retrieval quality measured yet. The table shows structural defects, not answer quality. Phase 7 (`eval-retrieval`) is where the choice is tested on questions; this decision stands until that shows otherwise.

## 2026-11-12 | Phase 4 | Chunker, comparison and two normalize fixes   (commit pending)

What: added `tokens.py`, `chunk.py`, `chunk_fixed.py`, `chunk_compare.py` and the commands `python main.py chunk` and `chunk-compare`. First full run: 5,243 chunks from 42 documents, max 480 tokens, none over the cap; `data/chunks.jsonl` and `data/chunks_manifest.json` written. Two fixes in `normalize.py`: dot leaders removed, padded table separators shortened. Re-ingested, so `data/md/` and `dataset_version` changed (`79b7bfa659c2`). 37 tests pass.

Why, by decision (each one came from a defect in a real run):
- **Boilerplate decided by the chunk's own heading, and boilerplate headings never parents.** First trial: 13 of 16 chunks of `gs01` were tagged boilerplate, because the converter made later sections children of "TABLE OF CONTENTS". Worse, a small table-of-contents chunk had absorbed the OFFERING SUMMARY table, which would have hidden the key listing data from search.
- **A small chunk absorbs only its own child subsection, never a sibling.** Merging siblings produced labels that said where the text did not come from.
- **Short title-like lines stay with the paragraph after them** (the converter leaves lines such as `INVESTMENT OVERVIEW` unmarked, so they ended the previous chunk).
- **Dot leaders removed in `normalize`.** 20 chunks were over the cap (max 710) because each dot of a table-of-contents leader is a token for the embedding model. This also cut boilerplate chunks from 367 to 61.
- **Row too wide: split into complete rows, label cells repeated.** The converter put some whole paragraphs into one table cell (Equiton, 4Q, LMIC). Cutting the row mid-text was rejected; it would break the "no cut table row" rule.
- **Padded table separators shortened** (`|-----|` to `|---|`); every dash is a token, about 100 tokens per OCR table chunk.
- **Chunk counts go to `data/chunks_manifest.json`**, not into the ingest manifest, so `chunk` never changes what `ingest` would archive.

Effect (comparison on 4 documents, details in the README): heading-aware chunks have 0 mid-sentence starts and 0 cut table rows. Fixed 400/80 windows had 23 and 35 on Retreat at Arcway, 49 and 28 on the first 40 pages of Centurion, and no section on any chunk. Price: heading-aware chunks are smaller (average 177 to 267 tokens against about 400), so there are more of them. Open: 3 chunks are under 20 tokens; the title-before-heading orphan is not fixed; spot-check by eye is still to do.

## 2026-11-12 | Phase 4 | Chunking decisions (plan only, no code yet)

What: two decisions recorded in `tasks/hw02-plan.md` before any chunking code.
1. Chunk sizes (target about 400 tokens, hard cap 480) are counted with the embedding model's own tokenizer (`BAAI/bge-small-en-v1.5`), not `cl100k_base`. The tokenizer sits behind one function in `tokens.py`. `tiktoken` is used only for the answer-model context budget in Phase 6.
2. A chunk with no heading gets `section` = `<title> > page <n>` for citations. The embedded text uses the title only, and each chunk carries `section_source: heading | page`.

Why:
- **Tokenizer:** `cl100k_base` undercounts number-heavy text such as financial tables, because the BERT-style tokenizer splits digits and punctuation into more pieces. A chunk of 480 by the plan's count can be over 512 for the model, which then silently drops the end of it. Counting with the model's tokenizer makes the cap match what the model really reads. It also keeps one embedding model in the whole app.
- **Section fallback:** the PDF converter finds headings unevenly (`gs01` has only a few). A page-based fallback keeps citations meaningful. Keeping the page number out of the embedded text stops a meaningless number from distorting search. `section_source` lets the comparison table still count how often headings were missing. Rejected: title only (vague citations), empty section (blank citations, and the plan's own empty-section check would fail).

Effect: none yet. Both decisions are checked by the Phase 4 comparison table, with the number of chunks over 512 model tokens expected to be 0.

## 2026-11-12 | Phase 3 | OCR command and OCR pages merged   (commit pending)

What: added `src/rag/ocr.py` and `python main.py ocr` (`--only`, `--limit`). It OCRs every page in the manifest's `ocr_required_pages` with Docling on CPU and writes `data/ocr/<doc_id>/page-<n>.md`; the next `ingest` merges them. Ran it on the corpus: 124 pages (131 total with the 7 trial pages), then re-ingested.

Why, by decision:
- **Separate command, engine injected** (`OcrEngine`), same pattern as the extractors. `ingest` never imports `ocr.py`, so ingest, CI and the later phases work without Docling or PyTorch OCR models; tests use a fake engine.
- **Full-page OCR, one page at a time**, because these pages have no usable text layer, and per-page output is written immediately so a 40-minute run can be interrupted and resumed.
- **Empty OCR result still writes an empty file**, and `ingest` turns that page into `blank`. Without this, photo pages stay `ocr_required` forever and every run offers to OCR them again.
- **Reads the manifest, not the audit log**, since the audit log now has one file per run.
- Known limit: OCR files are keyed by file name, not by file hash. If a PDF is replaced, its old OCR files must be deleted by hand.

Effect: 0 pages need OCR after re-ingest. 4 pages found no text (`gs06` page 10, Topaz pages 7, 9, 38). Outlined-text financial statements (RESCO, BGMFll) now come out as correct Markdown tables, with small glitches such as `$ 10,833,998$` in one cell. About 16 seconds per page on CPU. 22 tests pass.

## 2026-11-12 | Phase 2 | Versioned manifest, timestamped audit log   (commit pending)

What:
- `data/manifest.json` stays the latest manifest. When a run produces a different manifest, the old file is moved (not rewritten) to `data/manifests/manifest-<extract_version>-<hash8>.json`. An identical re-run archives nothing.
- The audit log moved from `data/audit.jsonl` to `data/audit/audit-<UTC timestamp>.jsonl`, one new file per run. `ingest()` takes an injectable `now` clock for tests.
- The original files were kept, not deleted: the first-run audit log is now `data/audit/audit-20261112T101935Z.jsonl` (timestamp of that run) and the first manifest, the `extract-v1` one with 97 `ocr_required` pages, is `data/manifests/manifest-extract-v1-252c2cb8.json`. Both were restored from commit `ed125e1`.

Why: when `EXTRACT_VERSION` changes, the old manifest was overwritten and there was no record of what the previous extraction produced (97 versus 131 `ocr_required` pages). The audit log is an event history of runs, so a run should not erase the previous one. `manifest.json` stays at a fixed path so later phases and CI always read the latest one. A snapshot per version was rejected because moving the old file keeps every distinct manifest, including two changes within one version.

Effect: audit files accumulate, one per run, so delete or ignore old ones if they grow. Audit files are no longer byte-identical between runs, because the file name carries the time. Phase 3 reads `ocr_required_pages` from the manifest, not from the audit log.

## 2026-11-12 | Phase 2 | Scanned-page rule: count vector drawings too   (commit pending)

What: a page with fewer than `MIN_CHARS_PER_PAGE` characters is `ocr_required` when it has an image OR more than `MIN_DRAWINGS_FOR_OCR` (20) vector paths. Otherwise it is `blank`. `Page` gained `n_drawings`; `EXTRACT_VERSION` went to `extract-v2`, so the extraction cache was rebuilt.

Why: 34 pages marked `blank` were really financial statements (RESCO pages 84-86 and 89-100, BGMFll pages 36-37 and 40-56). Their text had been converted to vector outlines, so they have no text layer and no images, and the image-only rule missed them. Options considered: (1) characters only, simplest but sends 4 genuinely empty pages to OCR; (2) characters plus drawings, chosen; (3) hand-OCR the 34 pages, rejected because the next outlined-text file would fail the same way.

Effect: in the RESCO and BGMFll trial, all 34 pages are now `ocr_required` and no blanks remain. Drawings are counted only for pages with no text and no images, since `get_drawings` is slow. New unit test builds a small PDF with a text page, a drawings-only page, an empty page and an image-only page. Threshold 20 is untuned: the 34 pages have 64 or more drawings, the 4 empty pages have 0.

## 2026-11-12 | Phase 2 | Full corpus ingested   (commit ed125e1)

What: ran `python main.py ingest --workers 1` on all 41 files. Output: 42 Markdown documents in `data/md/`, plus `data/manifest.json` and `data/audit.jsonl`. `dataset_version` is `5c38792da9b0`.

Why: `data/md/` is committed so CI and the later phases (chunk, index, evals) run without PDF extraction. Extraction is the slow step (about 25 minutes for the corpus).

Effect:
- 0 duplicates dropped, 0 files failed. The OAM file split into `@original` and `@addendum-1`, and the addendum starts at page 66.
- 97 pages are flagged `ocr_required` (the largest groups are LMIC pages 76-95, `gs03`, `gs06`, Topaz and `gs05`). Phase 3 handles them.
- Not done yet: the visual spot-check of `gs9`, a mid-size OM and a Centurion slice.

## 2026-11-12 | Phase 2 | Cleanup of partial output   (commit 7d039ae)

What: removed 8 `data/md/` files left by a failed first full run.

Why: they were committed by mistake and came from a partial run, so they did not match the manifest.

## 2026-11-12 | Phase 2 | Ingest code   (commit 6dd6162)

What: added `src/rag/` modules `meta`, `extract`, `normalize`, `versions`, `dedup`, `store`, `ingest`, and the `ingest` command (`--full`, `--workers`, `--only`, `--out`).

Why, by decision:
- **Few deep modules.** Each module has one small public function and hides its details (SOLID, deep vs shallow modules). Seven shallow files per step would have spread one idea across many places.
- **Injected extractors and paths** (`extractors=`, `IngestPaths`). A new format is one function plus one registry entry, and tests use fake extractors and a temp folder.
- **Only extraction is cached** (keyed by file hash + `EXTRACT_VERSION`). Normalize, version split and dedup run every time, so output depends only on inputs and code and a rule change needs no cache wipe.
- **Layout-aware `pymupdf4llm` with built-in OCR off.** Tables stay tables (`gs01` offering summary). OCR is a separate command so CI never needs it.
- **Scanned-page rule:** a page with fewer than `MIN_CHARS_PER_PAGE` characters and at least one image is `ocr_required`. With no image it is `blank`.
- **Version splits come from the catalog** (`versions:` in `doc_meta.yaml`). The marker detector only suggests splits in the audit log, so a table-of-contents line cannot split a document by accident.
- **Dedup keeps versions of one file apart** (OAM original and addendum). Near-duplicates use word 5-shingles with Jaccard above 0.8.
- **Table rows are never treated as repeated headers**, so a repeated column header stays as content.
- **`--only` and `--out`** let you trial a few files without touching `data/md/`.

Effect: 17 unit tests, no models or real PDFs needed. Open risk: running 6 extraction workers in parallel crashed with `BrokenProcessPool`; `--workers 1` is reliable. The pool does not yet recover from a dead worker.

## 2026-11 | Phase 1 | Scaffolding   (commit 95948e7)

What: `src/rag/config.py`, a stub for every RAG command in `main.py`, new dependencies, `.env.example`, README section, `tasks/hw02-plan.md`.

Why: the RAG work sits next to the block-1 service and must not change it, so RAG code lives in `src/rag/` and `src/rag_eval/`, and the answer eval is called `rag-eval` because `eval` already exists. Stubs keep the CLI honest: unimplemented commands exit with a message and code 2.

## Design decisions made before code (from the planning session)

| Decision | Choice | Why |
|---|---|---|
| Embeddings | `BAAI/bge-small-en-v1.5` via sentence-transformers | local, free, 512-token limit sets the chunk size |
| Vector store | Qdrant embedded | no server, filters on metadata |
| Search | vector + BM25 fused with RRF, then rerank top 20 to 5 | exact numbers and names need BM25, meaning needs vectors |
| Answer model | `gemini/gemini-2.5-flash` via LiteLLM | same setup as block 1 |
| Judge model | `openrouter/openai/gpt-4o-mini` | different family from the answer model |
| Scanned pages | recorded, then a separate `ocr` command (Docling) | the user did not want OCR skipped, and CI must not depend on it |
| HTML corpus | 10 saved listing pages in `data/html/` | public listings, kept static so runs are repeatable |
| Eval gate | tolerance 0.05 plus absolute floors | tolerates noise, still catches real regressions |
