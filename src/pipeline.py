import json
import time
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from .config import RESULTS, RunConfig
from .documents import list_sources, load_document
from .llm import build_messages, complete
from .prompts import load_prompt
from .schema import RealEstateListing


def _validate(content: str) -> tuple[RealEstateListing | None, str | None]:
    try:
        return RealEstateListing.model_validate_json(content), None
    except (ValidationError, ValueError) as e:
        return None, str(e)


def process(cfg: RunConfig, system_prompt: str, source_file: str) -> dict:
    record = {
        "source_file": source_file,
        "model": cfg.model,
        "input_mode": cfg.input_mode,
        "prompt_version": cfg.prompt_version,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "status": "failed",
        "repair_used": False,
        "output": None,
        "error": None,
        "latency_s": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0,
    }
    try:
        doc = load_document(source_file, cfg.input_mode, cfg.max_pages, cfg.max_tokens)
        record.update(pages_used=doc.pages_used, pages_total=doc.pages_total, doc_tokens=doc.tokens_used)
        messages = build_messages(system_prompt, doc)

        res = complete(cfg, messages)
        results = [res]
        parsed, err = _validate(res.content)

        if parsed is None:
            record["repair_used"] = True
            messages = messages + [
                {"role": "assistant", "content": res.content},
                {
                    "role": "user",
                    "content": f"Your output failed schema validation:\n{err}\nReturn corrected JSON only.",
                },
            ]
            res = complete(cfg, messages)
            results.append(res)
            parsed, err = _validate(res.content)

        record.update(
            latency_s=sum(r.latency_s for r in results),
            prompt_tokens=sum(r.prompt_tokens for r in results),
            completion_tokens=sum(r.completion_tokens for r in results),
            cost_usd=sum(r.cost_usd for r in results),
        )
        if parsed is not None:
            record.update(status="ok", output=parsed.model_dump(mode="json"))
        else:
            record["error"] = err
            record["raw_output"] = res.content
    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
    return record


def run(cfg: RunConfig, sources: list[str] | None = None) -> Path:
    sources = sources or list_sources()
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}_{cfg.name}"
    out_dir = RESULTS / run_id
    out_dir.mkdir(parents=True)
    (out_dir / "config.json").write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    system_prompt = load_prompt(cfg.prompt_version)

    with (out_dir / "run.jsonl").open("w", encoding="utf-8") as log:
        for i, src in enumerate(sources, 1):
            rec = process(cfg, system_prompt, src)
            (out_dir / (Path(src).stem + ".json")).write_text(
                json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            log.write(json.dumps({k: v for k, v in rec.items() if k not in ("output", "raw_output")}) + "\n")
            print(f"[{i}/{len(sources)}] {rec['status']:6} {rec['latency_s']:6.1f}s  {src}")
    return out_dir
