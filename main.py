import argparse
import json
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


def main():
    parser = argparse.ArgumentParser(description="Structured extraction service")
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

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
