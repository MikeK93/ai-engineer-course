import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import get_args

from pydantic import BaseModel

from .config import golden_path
from .schema import RealEstateListing


def _leaf_paths(model: type[BaseModel], prefix: str = "") -> list[str]:
    paths = []
    for name, field in model.model_fields.items():
        inner = next((a for a in get_args(field.annotation) if isinstance(a, type) and issubclass(a, BaseModel)), None)
        if inner is None and isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
            inner = field.annotation
        if inner is not None:
            paths += _leaf_paths(inner, f"{prefix}{name}.")
        else:
            paths.append(f"{prefix}{name}")
    return paths


FIELDS = _leaf_paths(RealEstateListing)


def _get(d: dict | None, path: str):
    for key in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def _norm(v):
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v).strip().lower() or None
    return v


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _empty(v) -> bool:
    if isinstance(v, list):
        return not any(_norm(x) for x in v)
    return _norm(v) is None


def _match(exp, pred) -> bool:
    if isinstance(exp, list) or isinstance(pred, list):
        return {_norm(x) for x in exp or [] if _norm(x)} == {_norm(x) for x in pred or [] if _norm(x)}
    exp, pred = _norm(exp), _norm(pred)
    if exp is None or pred is None:
        return exp is None and pred is None
    if _is_num(exp) and _is_num(pred):
        return math.isclose(exp, pred, rel_tol=0.01, abs_tol=1e-9)
    return exp == pred


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1)]


def load_golden(version: str | None = None) -> dict[str, dict]:
    rows = json.loads(golden_path(version).read_text(encoding="utf-8"))
    return {r["source_file"]: r["expected"] for r in rows if r["source_file"] != "SCHEMA"}


def evaluate(run_dir: Path, golden_version: str | None = None) -> dict:
    golden = load_golden(golden_version)
    records = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(run_dir.glob("*.json"))
        if p.name not in ("config.json", "metrics.json")
    ]
    records = [r for r in records if r["source_file"] in golden]
    if not records:
        raise ValueError("No golden-set documents in this run")

    correct, total = Counter(), Counter()
    false_null, hallucinated, errors = Counter(), Counter(), []
    for r in records:
        exp_doc, pred_doc = golden[r["source_file"]], r["output"] if r["status"] == "ok" else None
        for f in FIELDS:
            exp, pred = _get(exp_doc, f), _get(pred_doc, f)
            total[f] += 1
            if pred_doc is not None and _match(exp, pred):
                correct[f] += 1
                continue
            if pred_doc is None:
                continue  # failed record: counted wrong, not an individual error
            if _empty(pred) and not _empty(exp):
                false_null[f] += 1
            elif _empty(exp) and not _empty(pred):
                hallucinated[f] += 1
            errors.append({"source_file": r["source_file"], "field": f, "expected": exp, "predicted": pred})

    n = len(records)
    ok = [r for r in records if r["status"] == "ok"]
    lat = [r["latency_s"] for r in records]
    cost = sum(r["cost_usd"] for r in records)
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    return {
        "run_id": run_dir.name,
        "golden_version": golden_version or "v1",
        "model": cfg["model"],
        "input_mode": cfg["input_mode"],
        "prompt_version": cfg["prompt_version"],
        "temperature": cfg["temperature"],
        "top_p": cfg["top_p"],
        "documents": n,
        "valid_pct": 100 * len(ok) / n,
        "valid_first_try_pct": 100 * sum(1 for r in ok if not r["repair_used"]) / n,
        "failed": n - len(ok),
        "field_accuracy_pct": 100 * sum(correct.values()) / sum(total.values()),
        "per_field_accuracy_pct": {f: 100 * correct[f] / total[f] for f in FIELDS},
        "false_null": dict(false_null),
        "hallucinated": dict(hallucinated),
        "latency_p50_s": _percentile(lat, 50),
        "latency_p95_s": _percentile(lat, 95),
        "cost_per_1000_docs_usd": 1000 * cost / n,
        "errors": errors,
    }


def _md_cell(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ")


def render_report(m: dict) -> str:
    lines = [
        f"# Run {m['run_id']}",
        "",
        "| model | input | prompt | golden | temp | top_p | docs |",
        "|---|---|---|---|---|---|---|",
        f"| {m['model']} | {m['input_mode']} | {m['prompt_version']} | {m.get('golden_version', 'v1')} | {m['temperature']} | {m['top_p']} | {m['documents']} |",
        "",
        "## Metrics",
        "",
        f"- Field accuracy: {m['field_accuracy_pct']:.1f}%",
        f"- Valid responses: {m['valid_pct']:.1f}% (first try {m['valid_first_try_pct']:.1f}%, failed {m['failed']})",
        f"- Latency p50 / p95: {m['latency_p50_s']:.1f}s / {m['latency_p95_s']:.1f}s",
        f"- Cost per 1000 docs: ${m['cost_per_1000_docs_usd']:.2f}",
        "",
        "## Per-field accuracy",
        "",
        "| field | accuracy % | missed (null) | hallucinated |",
        "|---|---|---|---|",
    ]
    for f, acc in sorted(m["per_field_accuracy_pct"].items(), key=lambda kv: kv[1]):
        lines.append(f"| {f} | {acc:.0f} | {m['false_null'].get(f, 0)} | {m['hallucinated'].get(f, 0)} |")

    lines += ["", "## Errors", ""]
    errors = sorted(m["errors"], key=lambda e: (e["field"], e["source_file"]))
    if not errors:
        lines.append("No field mismatches.")
    else:
        lines += ["| Field | File | Expected | Got |", "|---|---|---|---|"]
        for e in errors:
            lines.append(
                f"| {e['field']} | {_md_cell(e['source_file'])} | {_md_cell(e['expected'])} | {_md_cell(e['predicted'])} |"
            )
    return "\n".join(lines) + "\n"


def write_report(run_dir: Path, m: dict) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report.md").write_text(render_report(m), encoding="utf-8")
