# RAG changelog

Every change to the RAG pipeline, newest first, with the reason. Block-1 extraction history is in `REPORT.md` and `prompts/`.

Entry: `## date | phase | title (commit)`, then **What**, **Why** (including what was rejected), **Effect** (metrics or open risk). One entry per meaningful change. Record metrics before and after when retrieval or answers change.

---

## 2026-11-17 | Phase 7 | Hand labels, and the s01 reference

What: `evals/labels.json` has 15 grades of the answers in `output/eval-v2-20261116T203842Z.json` (`correct`, `grounded`, a note). `p02` was removed after the disclaimer split fixed that abstain, and `f02` took its place. In `evals/testset.json`, the `s01` reference is "Plan to build 33 apartment units". The question, evidence, and `must` string `33 Apartment Units` are unchanged.
Why: the labels are the exam for the judge. They grade the answer text. `correct` is false for n03 (a computed cap rate), n04 (a carry allocation instead of an abstain), m01 (the unit mix), and m02 (the price without the amenities). The old s01 reference, "33 apartment units", read as if the units already exist, so the judge failed an answer that quoted the plan.
Effect: not calibrated yet. The string check for s01 still looks for `33 Apartment Units`.

## 2026-11-16 | Phase 6 | The answer sees the document title

What: each source block in the answer prompt is `source · embed_prefix · as_of`, then the chunk text. `embed_prefix` is the document title plus the section.
Why: search embeds that prefix, but the answer model only saw the file name and the section. For the Paramount lease, "Paramount" is in the title and not in the chunk text, so the model had `$7,937` and the fenced yard and still abstained.
Effect: not re-measured. The previous p03 abstain is the case this changes.

## 2026-11-15 | Phase 4 | A bare title leaves a disclaimer section

What: a plain all-caps title (`PROPERTY OVERVIEW`) that follows a disclaimer, confidentiality, or contents heading starts its own section. `PIPELINE_VERSION` is `rag-v3`.
Why: the converter left that title as a normal line, and the line before it was the OCR scrap `COFFESI`, so the 20-story description of 8000 Wisconsin Avenue stayed inside `NOTICE OF CONFIDENTIALITY` and was tagged boilerplate. Search drops boilerplate, so the floor count could not be retrieved.
Effect: that paragraph is now `OFFERING MEMORANDUM > PROPERTY OVERVIEW`, kind `content`. Re-chunk of the corpus: 4,628 to 4,629 chunks, boilerplate still 56.

## 2026-11-15 | Phase 7 | Answer scoring, judge, and gate

What: `score`, `judge`, `gate`, `run`, and `python main.py rag-eval [--repeat N]`. Facts match `must` groups after normalization, with prices and decimals within 1% and years and small counts exact. `cited` needs an evidence chunk among the citations. No-answer scores `abstain` only. The judge (`JUDGE_MODEL`, `prompts/rag/judge-v1/`) returns `reason` then `verdict`, with the reference in the prompt. Groundedness splits the answer into claims against the cited chunk text, and an abstain makes no judge call. The gate uses floors (`recall@5` 0.8, `pass` 0.7, `abstain` 1.0, `grounded` 0.85) and, once `evals/baseline.json` exists, a 0.05 tolerance with `false_abstain` lower-is-better plus per-case regressions. The report is `output/report-<prompt>-<timestamp>.md` and `output/eval-<prompt>-<timestamp>.json`, including cost per 1000 questions from the measured tokens.
Why: a keyword can pass for the wrong reason, and a right fact from the wrong document should fail. The judge covers the wording a string cannot see. Floors fail a weak run before a baseline exists. The report is written even when the gate fails, so the answers can be labeled.
Effect: one `rag-eval` on prompt v2, 29 questions, rerank. recall@5 0.92, pass 0.69, facts 0.76, cited 0.84, abstain 0.50, false_abstain 0.12, judge 0.69, grounded 0.92. Exact 6/6. Multi-chunk 0/3. The gate failed the initial floors on pass (0.69 < 0.70) and abstain (0.50 < 1.0). Answers cost $1.70 per 1000 questions, the judge $0.21. Floors stay as set until the hand labels.

## 2026-11-15 | Phase 6 | Answer prompt v2

What: `prompts/rag/v2/system.txt`. `PROMPT_VERSION` in `src/rag/llm_rag.py` is `v2`. `prompts/rag/v1/system.txt` is unchanged. v2 keeps every v1 rule and adds commercial real estate wording taken from `prompts/v4.md` and `src/schema.py`: a story is a floor (Single Story = 1, 21 stories = 21; also Floor Plans and Highlights), soft-story is a structural condition, lot size is the listing size in square feet (also acres, square meters, hectares), SF means square feet, units are property units, asking price is the numeric total price and usually sits in Pricing & Financial Summary, price per square foot and price per unit are separate, the seller is the broker, the property name is not the street address, property type is the listed type rather than a future plan, and Opportunity and Comparables sections are other properties.
Why: questions say "floors", "lot size", and "asking price" while the brochures say "20-story", "Lot Size", and "Asking Price". The glossary only tells the model how to read those words. Extractor exceptions (inferring country and condition) stay out, so a missing fact is still "Not in the documents."
Effect: not measured. Answer accuracy is still open.

## 2026-11-15 | Phase 7 | Retrieval metrics

What: `src/rag_eval/retrieval_eval.py` and `python main.py eval-retrieval`. Scores the answerable cases only (a no-answer row has no relevant chunk). recall@k is the mean share of relevant chunk ids in the top k. MRR is the mean of 1/rank of the first one, or 0. A miss is a question missing at least one of those ids. A case `doc_type` is applied with the same `Filters` as `search`. The table is also written to `output/retrieval-<timestamp>.json`. No answer model call.
Why: an answer score cannot tell a missed chunk from a bad generation. The metric function takes rankings and nothing else, so the 0.67 / 0.50 check does not load the index.
Effect: 25 answerable questions, k=5. Vector and rerank averages include loading the model on the first query.

| Config | recall@5 | MRR | ms/query | Miss |
|---|---|---|---|---|
| vector | 0.85 | 0.75 | 813.6 | p02, p03, o02, m01, m02, m03 |
| bm25 | 0.84 | 0.66 | 18.1 | p02, p05, o02, m03, f02 |
| hybrid | 0.88 | 0.85 | 254.0 | p02, p05, o02, m03 |
| rerank | 0.92 | 0.82 | 3061.8 | p02, m02, m03 |

p02 (Wisconsin floors) is missing in every config. m03 lists more evidence chunks than k=5 can hold, so it stays a partial miss. Rerank raises recall and drops m02, which hybrid had found.

## 2026-11-15 | Phase 7 | Test-set lint

What: `src/rag_eval/lint.py` and `python main.py lint-testset`. Each evidence quote must be in exactly one expected document and in no other. `must` groups are AND, options inside a group are OR, and a hit has to be in a chunk that contains the quote. A heading counts, because retrieval searches `embed_prefix` plus the text. No-answer rows have no evidence, no `must`, and the abstain sentence. Chunk ids are returned at run time and are not written into `evals/testset.json`.
Why: a quote that also sits in a second document can make retrieval credit the wrong file. Checking that before scoring keeps the test set editable without storing chunk ids that go stale on the next chunk run.
Effect: 29 cases, 0 errors. Every evidence quote is in exactly one expected document, and every `must` string is in those chunks.

## 2026-11-15 | Phase 6 | Answer path

What: `context`, `llm_rag`, `answer`; command `ask` (default `--config rerank`, same filters as `search`, `--log`). Retrieved chunks are packed in rank order under 2,500 tokens (`tiktoken` `cl100k_base`), labelled `S1..Sn`, header `source · section · as_of`. The model (`RAG_MODEL`, prompt `prompts/rag/v1/system.txt`) is called with `response_format=RagAnswer` at temperature 0. The body is validated with `model_validate_json`; if that fails, fences and surrounding text are trimmed and validation is tried once more. Citations are stripped, unknown labels dropped, duplicates removed, then mapped back to `chunk_id`, source, section. Each question is appended to `output/answers-*.jsonl`.
Why:
- `src/llm.py` stays the block-1 extractor. The answer call is a separate LiteLLM request.
- Empty retrieval, or a `found` answer with no valid label, returns the constant `Not in the documents.` and does not trust the model text. A real abstain also skips inventing citations.
- Prompt v1: only the `<sources>` block, copy numbers and addresses exactly, the named property beats a comparable, the later `as_of` wins and the older figure is named, fund text is about the fund and listing text about the building, a similar property is not an answer. History of that prompt lives in this file.
Effect: `1028 Johnson Street` asking price came back `$1,189,900`, cited `...Johnson_Street...#0` (S1, p.1, as_of 2026-08-10). Four of the five packed chunks were other properties; only S1 was cited. A made-up address (`1 Imaginary Lane`) was answered `Not in the documents.` with no citations, after five unrelated hits (rerank scores all negative). Model calls: 1,722 and 2,430 prompt tokens, about $0.001 each, 1.9 s and 1.5 s. Answer accuracy is not measured yet (Phase 7).

## 2026-11-13 | Phase 5 | Index and retrieval

What: `embed`, `bm25`, `index`, `retrieve`, `rerank`; commands `index` and `search --config vector|bm25|hybrid|rerank` (`-k`, `--doc-type`, `--as-of-min`, `--include-boilerplate`, `--include-skip`). Hybrid = vector top 20 + BM25 top 20, RRF `1/(60+rank)`. Rerank = cross-encoder (`ms-marco-MiniLM-L-6-v2`) over the top 20 hybrid hits, best 5 kept.
Why:
- Embedded string and BM25 input are the same (`embed_prefix` + text); the stored payload keeps clean text.
- Vectors are cached in SQLite by model + text, so a rebuild embeds only new or changed chunks and a model change never reuses old vectors. The query gets the bge query prefix.
- BM25 tokenizer keeps `$1,250,000`, `80231`, `9850` whole; plain word splitting would break exactly the figures questions ask about.
- One `Filters` object feeds both Qdrant and BM25, applied before ranking, so a filtered-out chunk never takes a place. Default: no boilerplate and no `skip_candidate` (comparables); both can be switched on. `as_of` is stored also as a number (`as_of_num`) for date filters.
- The index is rebuilt from `chunks.jsonl` only and never committed. Models and Qdrant are injected, so the 12 new tests need no downloads.
Effect: 4,628 chunks indexed. First build took about 27 min on CPU; reruns reuse the cache. Spot checks: the `1028 Johnson Street` price chunk is rank 1 in all four configs; `gs10` price chunk is rank 1 (hybrid); "can investors sell shares whenever they want" finds the no-trading-market risk chunks (rerank); the listing + 2026 filter returns only listings. Not measured yet: recall@k and MRR (Phase 7). Seen: rerank can still put an off-topic chunk third.

## 2026-11-13 | Phase 4 | Chunk manifest archived like the ingest manifest

What: `chunk` writes the latest summary to `data/chunks_manifest.json`; a different previous one is moved to `data/manifests/chunks-manifest-<pipeline_version>-<hash>.json`.
Why: the summary was overwritten on every run. Only `chunk` writes this file.

## 2026-11-13 | Phase 2 + 4 | Clean-up after checking chunks against the Markdown

What:
- Ingest: no blank lines between list items, empty bullets removed; private-use glyphs, `U+FFFD` and control characters removed; a page that is mostly private-use glyphs (30%) becomes `ocr_required`.
- Chunk: a heading that carries a figure (`ASKING PRICE: $1,189,900`, `37,312 SF`) stays in the text; sentences split by a page break are rejoined; a sentence is never cut while it fits the model's 512 tokens.
- After cutting, per document: comparables tagged `skip_candidate` + `skip_reason`; pagination-only chunks dropped; chunks under 3 words (no digit) dropped; exact duplicates dropped; chunks under 50 word-tokens squashed into a neighbour (heading kept as a text line). `PIPELINE_VERSION` = `rag-v2`.

Why: review found two missing prices (headings with no body), page-number footers, 156 duplicates, 63 mid-sentence starts, title-only chunks, and 36 RESCO pages of pure private-use glyphs. Garbled pages go to OCR, not to nothing. Comparables are tagged, not deleted; Phase 5 decides. Duplicates are removed inside one document only, so each document stays citable. Rejected: counting table separators as size; keeping every heading with a digit (broke `ITEM 2` sections).
Effect: 5,243 to 4,628 chunks (after the RESCO OCR pages were merged). Bad characters: 0. Lowercase starts: 63 to 18, all single legal sentences over 512 tokens. About 300 chunks under 30 words are table fragments that cannot merge without passing the cap.

## 2026-11-12 | Phase 4 | DECISION: production chunking is "by heading"

What: `chunk` cuts by heading. Fixed 400/80 windows stay only as a baseline in `measurements/chunking/` (`python main.py chunk-compare`, documents in `targets.yaml`; `chunk` does not read it). Sizes use the bge tokenizer.

| Document | Strategy | Chunks | Avg tokens | Max | Mid-sentence starts | Cut table rows | Empty section |
|---|---|---|---|---|---|---|---|
| gs01 | by heading | 19 | 177 | 394 | 0 | 0 | 0 |
| gs01 | fixed 400/80 | 10 | 382 | 400 | 1 | 4 | 10 |
| gs9 | by heading | 4 | 227 | 394 | 0 | 0 | 0 |
| gs9 | fixed 400/80 | 3 | 350 | 400 | 1 | 0 | 3 |
| Retreat at Arcway | by heading | 80 | 267 | 477 | 0 | 0 | 0 |
| Retreat at Arcway | fixed 400/80 | 61 | 398 | 400 | 23 | 35 | 61 |
| Centurion p1-40 | by heading | 137 | 236 | 479 | 0 | 0 | 0 |
| Centurion p1-40 | fixed 400/80 | 98 | 398 | 400 | 49 | 28 | 98 |

Why: no mid-sentence starts, no cut table rows, every chunk has a section for citations, and `embed_prefix` (title + section) gives numbers context. Tables carry the answers; cutting a row separates a number from its label.
Cost: chunks are smaller and 30 to 40 percent more numerous. Cheap at this size. If recall is weak in Phase 7, merge small neighbours first, not return to fixed windows.
Limit: 4 documents, structure only, no retrieval quality yet. Phase 7 tests the choice.

## 2026-11-12 | Phase 4 | Chunker and two normalize fixes

What: `tokens.py`, `chunk.py`, commands `chunk` and `chunk-compare`. First run: 5,243 chunks, none over the cap. `normalize` now removes dot leaders and shortens padded table separators.
Why, each from a defect in a real run:
- Boilerplate is decided by the chunk's own heading, and boilerplate headings are never parents: 13 of 16 `gs01` chunks were tagged boilerplate, and a table-of-contents chunk had absorbed the OFFERING SUMMARY table.
- A small chunk absorbs only its own child subsection, never a sibling (siblings gave wrong labels).
- Title-like lines (`INVESTMENT OVERVIEW`) stay with the paragraph after them.
- Dot leaders removed: each dot is a token; 20 chunks were over the cap (max 710). Padded `|-----|` shortened for the same reason (about 100 tokens per OCR table chunk).
- A too-wide row (a paragraph in one cell) becomes several complete rows with label cells repeated; cutting mid-row was rejected.
- Chunk counts go to `chunks_manifest.json`, so `chunk` never changes what `ingest` archives.

## 2026-11-12 | Phase 4 | Chunking decisions (before code)

What:
1. Sizes (target about 400, cap 480 tokens) are counted with the embedding model's tokenizer (`BAAI/bge-small-en-v1.5`), not `cl100k_base`. `tiktoken` is for the Phase 6 context budget only.
2. A chunk with no heading gets `section` = `<title> > page <n>`; the embedded text uses the title only; `section_source` is `heading` or `page`.

Why: `cl100k_base` undercounts number-heavy tables, so a 480 chunk can exceed 512 model tokens and silently lose its end. One embedding model in the app. Page-based sections keep citations meaningful without putting a page number into the embedding. Rejected: title only (vague citations), empty section (blank citations).

## 2026-11-12 | Phase 3 | OCR command

What: `python main.py ocr` (`--only`, `--limit`) OCRs `ocr_required` pages with Docling on CPU into `data/ocr/<doc_id>/page-<n>.md`; the next `ingest` merges them. 131 pages done.
Why: a separate command with an injected engine, so ingest, CI and later phases never need Docling. Pages are written one by one so a long run can resume. An empty result still writes an empty file, so the page becomes `blank` and is not offered again. It reads the manifest, not the audit log.
Effect: 0 pages need OCR; 4 pages found no text. About 16 s per page. Limit: OCR files are keyed by file name, so replacing a PDF means deleting its OCR folder by hand.

## 2026-11-12 | Phase 2 | Versioned manifest, timestamped audit log

What: `manifest.json` stays the latest; a different previous one is moved to `data/manifests/manifest-<extract_version>-<hash8>.json`. Audit logs are `data/audit/audit-<UTC timestamp>.jsonl`, one per run.
Why: a changed `EXTRACT_VERSION` overwrote the old manifest (97 vs 131 `ocr_required` pages) and each run erased the last audit log. Old files were kept, not deleted.

## 2026-11-12 | Phase 2 | Scanned-page rule counts vector drawings

What: a page under 50 characters is `ocr_required` with an image or more than 20 vector paths; otherwise `blank`. `EXTRACT_VERSION` = `extract-v2`.
Why: 34 "blank" pages (RESCO, BGMFll) were financial statements drawn as outlines. Rejected: characters only (sends 4 truly empty pages to OCR); hand-OCR (next file fails the same way).
Effect: all 34 are `ocr_required`. Threshold 20 is untuned (the 34 pages have 64 or more paths, empty pages 0).

## 2026-11-12 | Phase 2 | Full corpus ingested (ed125e1) and cleanup (7d039ae)

What: 41 files to 42 Markdown documents (OAM split into `@original` and `@addendum-1` at page 66), 0 duplicates, 0 failures. Removed 8 partial `data/md/` files from a failed first run.
Why: `data/md/` is committed so CI and later phases skip the slow extraction (about 25 minutes).

## 2026-11-12 | Phase 2 | Ingest code (6dd6162)

What: `meta`, `extract`, `normalize`, `versions`, `dedup`, `store`, `ingest`; command `ingest` (`--full`, `--workers`, `--only`, `--out`).
Why:
- Few deep modules with one small public function each, not many shallow files.
- Injected extractors and paths: a new format is one function, tests use fakes and a temp folder.
- Only extraction is cached (file hash + `EXTRACT_VERSION`); the rest reruns, so a rule change needs no cache wipe.
- `pymupdf4llm` with OCR off keeps tables as tables; OCR is a separate command.
- Version splits come from `versions:` in `doc_meta.yaml`; the marker detector only suggests, so a table-of-contents line cannot split a document.
- Dedup keeps versions of one file apart; near-duplicates use word 5-shingles, Jaccard above 0.8. Repeated table rows are content, not headers.
Effect: open risk: 6 parallel workers crashed with `BrokenProcessPool`; use `--workers 1`.

## 2026-11 | Phase 1 | Scaffolding (95948e7)

What: `src/rag/config.py`, stubs for every RAG command (exit code 2), dependencies, `.env.example`, README section, plan.
Why: RAG code lives in `src/rag/` and does not touch block 1; the answer eval is `rag-eval` because `eval` exists.

## Design decisions made before code

| Decision | Choice | Why |
|---|---|---|
| Embeddings | `BAAI/bge-small-en-v1.5`, sentence-transformers | local, free; 512-token limit sets chunk size |
| Vector store | Qdrant embedded | no server, metadata filters |
| Search | vector + BM25 fused with RRF, rerank top 20 to 5 | exact numbers need BM25, meaning needs vectors |
| Answer model | `gemini/gemini-2.5-flash` via LiteLLM | same setup as block 1 |
| Judge model | `openrouter/openai/gpt-4o-mini` | different family from the answer model |
| Scanned pages | recorded, then a separate `ocr` command (Docling) | OCR not skipped; CI must not depend on it |
| HTML corpus | 10 saved listing pages in `data/html/` | static, so runs repeat |
| Eval gate | tolerance 0.05 plus absolute floors | tolerates noise, catches real regressions |
