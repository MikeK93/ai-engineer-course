import argparse
import json

from src.config import GOLDEN, load_config
from src.documents import extract_text, list_sources
from src.config import PDFS


def cmd_extract(_):
    for name in list_sources():
        pages = extract_text(PDFS / name)
        print(f"{len(pages):4} pages  {name}")


def cmd_run(args):
    from src.pipeline import run

    cfg = load_config(args.config)
    sources = list_sources()
    if args.golden:
        sources = [r["source_file"] for r in json.loads(GOLDEN.read_text(encoding="utf-8")) if r["source_file"] != "SCHEMA"]
    if args.limit:
        sources = sources[: args.limit]
    out = run(cfg, sources)
    print(f"Results: {out}")


def cmd_eval(args):
    from pathlib import Path

    from src.evaluate import evaluate, write_report

    run_dir = Path(args.run_dir)
    metrics = evaluate(run_dir)
    write_report(run_dir, metrics)
    print((run_dir / "report.md").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Structured extraction service")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("extract", help="Extract and cache text from all PDFs").set_defaults(fn=cmd_extract)
    p = sub.add_parser("run", help="Run extraction with a config")
    p.add_argument("--config", required=True)
    p.add_argument("--golden", action="store_true", help="Only the golden-set documents")
    p.add_argument("--limit", type=int, help="Only the first N documents")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("eval", help="Score a run against the golden set and write its report")
    p.add_argument("run_dir")
    p.set_defaults(fn=cmd_eval)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
