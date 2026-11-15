import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from src.config import PDFS, ROOT, golden_path, latest_prompt_version, load_config, model_tag, model_variants
from src.documents import extract_text, list_sources


def _golden_sources(version: str | None = None) -> list[str]:
    rows = json.loads(golden_path(version).read_text(encoding="utf-8"))
    return [r["source_file"] for r in rows if r["source_file"] != "SCHEMA"]


def _score(run_dir: Path, golden_version: str | None = None) -> None:
    from src.evaluate import evaluate, write_report

    try:
        write_report(run_dir, evaluate(run_dir, golden_version))
        print(f"Report: {run_dir / 'report.md'}")
    except ValueError:
        print("No golden-set documents in this run; skipping scoring")


def cmd_extract(_):
    for name in list_sources():
        pages = extract_text(PDFS / name)
        print(f"{len(pages):4} pages  {name}")


def _with_input(cfg, input_mode: str | None):
    if not input_mode:
        return cfg
    return replace(cfg, input_mode=input_mode, name=f"{cfg.name}_{input_mode}")


def cmd_run(args):
    from src.pipeline import run

    cfg = _with_input(load_config(args.config), args.input)
    if args.prompt:
        prompt = latest_prompt_version() if args.prompt == "latest" else args.prompt
        cfg = replace(cfg, prompt_version=prompt, name=f"{cfg.name}_{prompt}")
    sources = _golden_sources(args.golden_version) if args.golden else list_sources()
    if args.limit:
        sources = sources[: args.limit]
    out = run(cfg, sources)
    print(f"Results: {out}")
    _score(out, args.golden_version)


def cmd_eval(args):
    from src.evaluate import evaluate, write_report

    run_dir = Path(args.run_dir)
    write_report(run_dir, evaluate(run_dir, args.golden_version))
    print((run_dir / "report.md").read_text(encoding="utf-8"))


def cmd_grid(args):
    from src.pipeline import run

    config_paths = args.configs or sorted(str(p) for p in (ROOT / "configs").glob("*.yaml"))
    sources = list_sources() if args.all else _golden_sources(args.golden_version)
    if args.limit:
        sources = sources[: args.limit]
    for path in config_paths:
        base = _with_input(load_config(path), args.input)
        models = model_variants(base.model_env)
        prompts = [latest_prompt_version() if p == "latest" else p for p in args.prompts or []]
        for model in models:
            tagged = base if len(models) == 1 else replace(base, model=model, name=f"{base.name}_{model_tag(model)}")
            for prompt in prompts or [tagged.prompt_version]:
                cfg = tagged if not prompts else replace(tagged, prompt_version=prompt, name=f"{tagged.name}_{prompt}")
                print(f"\n== {cfg.name}: {cfg.model} | {cfg.input_mode} | {cfg.prompt_version} | t={cfg.temperature} top_p={cfg.top_p}")
                out = run(cfg, sources)
                _score(out, args.golden_version)
    print("\nDone. Build the summary with: python main.py report --all")


def cmd_report(_):
    from src.report import build_report

    print(f"Updated {build_report()}")


# --- RAG pipeline commands (tasks/hw02-plan.md). Stubs until their phase lands. ---
def cmd_ingest(args):
    from src.rag.config import IngestPaths
    from src.rag.ingest import ingest, summarize

    paths = IngestPaths()
    if args.out:
        out = Path(args.out)
        paths = replace(paths, md=out / "md", manifest=out / "manifest.json",
                        manifest_dir=out / "manifests", audit_dir=out / "audit")
    manifest = ingest(full=args.full, workers=args.workers, only=args.only, paths=paths)
    print(summarize(manifest))
    print(f"Details: {paths.manifest} (also in {paths.manifest_dir}) and the newest file in {paths.audit_dir}")
    if any(f["status"] == "error" for f in manifest["files"].values()):
        raise SystemExit(1)


def cmd_ocr(args):
    from src.rag.ocr import run_ocr

    report = run_ocr(only=args.only, limit=args.limit)
    print(f"{report['done']} pages OCRed ({report['empty']} found no text), {report['pending']} still pending. "
          "Now run `python main.py ingest` to merge them.")


def cmd_chunk(args):
    from src.rag.chunk import chunk_corpus
    from src.rag.config import ChunkPaths

    paths = ChunkPaths()
    if args.out:
        out = Path(args.out)
        paths = replace(paths, chunks=out / "chunks.jsonl", summary=out / "chunks_manifest.json",
                        summary_dir=out / "manifests")
    summary = chunk_corpus(paths=paths, only=args.only)
    print(f"{summary['n_chunks']} chunks ({summary['n_boilerplate']} boilerplate, {summary['n_ocr']} from OCR pages, "
          f"{summary['n_page_sections']} with a page section), max {summary['max_tokens']} tokens")
    print(f"Written: {paths.chunks} and {paths.summary}")
    if summary["over_cap"]:
        print(f"{len(summary['over_cap'])} chunks are over the cap, for example {summary['over_cap'][:3]}")
        raise SystemExit(1)


def cmd_chunk_compare(args):
    from measurements.chunking.compare import TARGETS, compare_chunkers

    config = Path(args.config) if args.config else TARGETS
    print(compare_chunkers(config=config))
    print(f"Compared the documents in {config}. Also written to output/chunk-compare.md")


def cmd_index(args):
    from src.rag.config import IndexPaths
    from src.rag.embed import Embedder
    from src.rag.index import build_index, open_client
    from src.rag.store import read_jsonl

    paths = IndexPaths()
    if not paths.chunks.is_file():
        raise SystemExit(f"{paths.chunks} not found. Run `python main.py chunk` first.")
    chunks = read_jsonl(paths.chunks)
    n = build_index(chunks, Embedder(cache=paths.embedding_cache), open_client(paths.index))
    print(f"{n} chunks indexed in {paths.index} (vectors cached in {paths.embedding_cache}). "
          "BM25 is rebuilt in memory from chunks.jsonl on every search.")


def cmd_ask(args):
    from datetime import datetime, timezone

    from src.rag.answer import answer_question, answers_path
    from src.rag.config import IndexPaths
    from src.rag.index import Filters
    from src.rag.retrieve import load_retriever

    paths = IndexPaths()
    if not paths.index.exists():
        raise SystemExit(f"{paths.index} not found. Run `python main.py index` first.")
    sys.stdout.reconfigure(errors="replace")
    filters = Filters(doc_types=tuple(args.doc_type) if args.doc_type else None, as_of_min=args.as_of_min,
                      include_boilerplate=args.include_boilerplate, include_skip=args.include_skip)
    log_path = Path(args.log) if args.log else answers_path(datetime.now(timezone.utc))
    result = answer_question(args.question, retriever=load_retriever(paths, log=print), config=args.config,
                             filters=filters, k=args.k, log_path=log_path, log=print)
    print(json.dumps(result.to_log(), ensure_ascii=False, indent=2))
    print(f"Log: {log_path}")


def cmd_search(args):
    from src.rag.config import IndexPaths
    from src.rag.index import Filters
    from src.rag.retrieve import load_retriever

    paths = IndexPaths()
    if not paths.index.exists():
        raise SystemExit(f"{paths.index} not found. Run `python main.py index` first.")
    sys.stdout.reconfigure(errors="replace")           # chunk text may hold characters the console cannot show
    filters = Filters(doc_types=tuple(args.doc_type) if args.doc_type else None, as_of_min=args.as_of_min,
                      include_boilerplate=args.include_boilerplate, include_skip=args.include_skip)
    hits = load_retriever(paths, log=print).search(args.query, args.config, filters=filters, k=args.k)
    if not hits:
        print("No hits.")
    for rank, hit in enumerate(hits, start=1):
        c = hit.chunk
        where = f"{c['source']} p.{c['page_start']}" + (f"-{c['page_end']}" if c["page_end"] != c["page_start"] else "")
        print(f"{rank}. {hit.score:.4f}  {dict(hit.ranks)}  {c['chunk_id']}")
        print(f"   {where} | {c['section']} | {c['doc_type']} | as_of {c['as_of']}")
        print(f"   {' '.join(c['text'].split())[:240]}")


RAG_STUBS = {
    "eval-retrieval": (7, "recall@k and MRR for each search config on the test set"),
    "rag-eval": (7, "Score RAG answers on the test set, run the judge, check the gate"),
    "rag-all": (9, "Run ingest, chunk, index and both evals in one go"),
}


def cmd_rag_stub(args):
    phase, what = RAG_STUBS[args.cmd]
    print(f"`{args.cmd}` is not implemented yet. It lands in Phase {phase} of tasks/hw02-plan.md: {what}.")
    raise SystemExit(2)


def _add_rag_stubs(sub):
    for name, (phase, what) in RAG_STUBS.items():
        p = sub.add_parser(name, help=f"[RAG, phase {phase}, not implemented] {what}")
        p.set_defaults(fn=cmd_rag_stub)


def main():
    parser = argparse.ArgumentParser(description="Structured extraction service and RAG pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("extract", help="Extract and cache text from all PDFs").set_defaults(fn=cmd_extract)

    p = sub.add_parser("run", help="Run extraction with a config, then score it")
    p.add_argument("--config", required=True)
    p.add_argument("--golden", action="store_true", help="Only the golden-set documents")
    p.add_argument("--limit", type=int, help="Only the first N documents")
    p.add_argument("--golden-version", default="v1", help="Golden set version: v1 = golden.json, vN = golden_vN.json")
    p.add_argument("--input", choices=["text", "pdf"], help="Override input_mode from the config")
    p.add_argument("--prompt", help="Prompt version override, e.g. v2 or latest")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("eval", help="Score a run against the golden set and write its report")
    p.add_argument("run_dir")
    p.add_argument("--golden-version", default="v1", help="Golden set version: v1 = golden.json, vN = golden_vN.json")
    p.set_defaults(fn=cmd_eval)

    p = sub.add_parser("grid", help="Run several configs (and prompt versions) on the golden set")
    p.add_argument("--configs", nargs="+", help="Config files; default is every file in configs/")
    p.add_argument("--prompts", nargs="+", help="Prompt versions to run for each config, e.g. v1 v2")
    p.add_argument("--all", action="store_true", help="Run on all documents instead of the golden set")
    p.add_argument("--limit", type=int, help="Only the first N documents")
    p.add_argument("--golden-version", default="v1", help="Golden set version: v1 = golden.json, vN = golden_vN.json")
    p.add_argument("--input", choices=["text", "pdf"], help="Override input_mode from each config")
    p.set_defaults(fn=cmd_grid)

    p = sub.add_parser("report", help="Aggregate all scored runs into REPORT.md")
    p.add_argument("--all", action="store_true", required=True, help="Include every run in results/")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("ingest", help="[RAG] Extract PDFs and HTML to Markdown in data/md/ (normalize, dedup, split versions)")
    p.add_argument("--full", action="store_true", help="Ignore the extraction cache and re-extract every file")
    p.add_argument("--workers", type=int, default=1, help="Parallel extraction processes")
    p.add_argument("--only", nargs="+", help="Trial run: only catalog files whose path contains one of these texts")
    p.add_argument("--out", help="Write md/, manifest.json, manifests/ and audit/ here instead of data/")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("ocr", help="[RAG] OCR the pages ingest marked ocr_required (needs requirements-ocr.txt)")
    p.add_argument("--only", nargs="+", help="Only files whose path contains one of these texts")
    p.add_argument("--limit", type=int, help="Stop after this many pages (trial run)")
    p.set_defaults(fn=cmd_ocr)

    p = sub.add_parser("chunk", help="[RAG] Chunk data/md/ by heading into data/chunks.jsonl")
    p.add_argument("--only", nargs="+", help="Trial run: only documents whose id contains one of these texts")
    p.add_argument("--out", help="Write chunks.jsonl and chunks_manifest.json here instead of data/")
    p.set_defaults(fn=cmd_chunk)

    p = sub.add_parser("chunk-compare", help="[RAG] Compare heading-aware chunks with fixed windows")
    p.add_argument("--config", help="YAML of documents to compare (default measurements/chunking/targets.yaml)")
    p.set_defaults(fn=cmd_chunk_compare)

    sub.add_parser("index", help="[RAG] Embed data/chunks.jsonl into the Qdrant index (index/)").set_defaults(fn=cmd_index)

    p = sub.add_parser("search", help="[RAG] Search the index and print the top hits")
    p.add_argument("query")
    p.add_argument("--config", choices=["vector", "bm25", "hybrid", "rerank"], default="hybrid")
    p.add_argument("-k", type=int, default=5, help="Hits to print")
    p.add_argument("--doc-type", nargs="+", help="Only these document types, e.g. listing single_asset_om")
    p.add_argument("--as-of-min", help="Only documents dated on or after this, e.g. 2024 or 2024-06")
    p.add_argument("--include-boilerplate", action="store_true", help="Also search disclaimers and tables of contents")
    p.add_argument("--include-skip", action="store_true", help="Also search sale / rent comparables")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("ask", help="[RAG] Answer a question from the index, with citations")
    p.add_argument("question")
    p.add_argument("--config", choices=["vector", "bm25", "hybrid", "rerank"], default="rerank")
    p.add_argument("-k", type=int, default=5, help="Chunks retrieved before packing the context")
    p.add_argument("--doc-type", nargs="+", help="Only these document types, e.g. listing single_asset_om")
    p.add_argument("--as-of-min", help="Only documents dated on or after this, e.g. 2024 or 2024-06")
    p.add_argument("--include-boilerplate", action="store_true")
    p.add_argument("--include-skip", action="store_true", help="Also use sale / rent comparables")
    p.add_argument("--log", help="Append the JSONL record here (default output/answers-<timestamp>.jsonl)")
    p.set_defaults(fn=cmd_ask)

    _add_rag_stubs(sub)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
