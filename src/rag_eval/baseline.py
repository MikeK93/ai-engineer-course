"""Turn a repeated eval into the gate's baseline. Public API: `from_eval`, `source_metadata`.

`evals/baseline.json` is the snapshot later runs are compared with. Metrics are the averages already
stored on the eval. `passed` is every id that passed all repeats: it passed the saved run and it is
not flaky. A flaky id passed sometimes, so a later failure of it is not a regression.

`evals/baseline.source-metadata.json` is the per-case record of that same saved run. The report reads
it to name a degradation. It is committed next to the baseline, so the comparison does not depend on
`output/`.
"""

import json
from pathlib import Path

from src.rag.config import EVALS_DIR

BASELINE = EVALS_DIR / "baseline.json"
METADATA_NAME = "baseline.source-metadata.json"
METRIC_KEYS = ("pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded", "recall@5")
CASE_FIELDS = (
    "id", "kind", "pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded",
    "answer", "cited_ids", "relevant", "must", "reference",
)


def from_eval(payload: dict, *, source: str = "") -> dict:
    """The baseline dict for one `eval-*.json` payload."""
    metrics = payload.get("metrics") or {}
    flaky = list((payload.get("stability") or {}).get("flaky") or [])
    shaky = set(flaky)
    passed = [row["id"] for row in payload.get("cases") or [] if row.get("pass") and row["id"] not in shaky]
    return {
        "source": source,
        "prompt": payload.get("prompt"),
        "repeat": payload.get("repeat"),
        "k": payload.get("k"),
        "metrics": {key: metrics[key] for key in METRIC_KEYS if isinstance(metrics.get(key), (int, float))},
        "passed": passed,
        "flaky": flaky,
    }


def metadata_path(baseline_path: Path = BASELINE) -> Path:
    """The per-case file that sits next to a baseline file."""
    return baseline_path.with_name(METADATA_NAME)


def source_metadata(payload: dict, *, source: str = "") -> dict:
    """Per-case scores and answers from the saved run. Tokens and judge text are left out."""
    cases = [{key: row.get(key) for key in CASE_FIELDS} for row in payload.get("cases") or []]
    return {
        "source": source,
        "prompt": payload.get("prompt"),
        "repeat": payload.get("repeat"),
        "k": payload.get("k"),
        "cases": cases,
    }


def write_baseline(eval_path: Path, *, dest: Path = BASELINE) -> dict:
    """Write the gate snapshot and the per-case metadata from one eval JSON."""
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    baseline = from_eval(payload, source=eval_path.name)
    meta = source_metadata(payload, source=eval_path.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    metadata_path(dest).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return baseline
