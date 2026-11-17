"""Turn a repeated eval into the gate's baseline. Public API: `from_eval`.

`evals/baseline.json` is the snapshot later runs are compared with. Metrics are the averages already
stored on the eval. `passed` is every id that passed all repeats: it passed the saved run and it is
not flaky. A flaky id passed sometimes, so a later failure of it is not a regression.
"""

import json
from pathlib import Path

from src.rag.config import EVALS_DIR

BASELINE = EVALS_DIR / "baseline.json"
METRIC_KEYS = ("pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded", "recall@5")


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


def write_baseline(eval_path: Path, *, dest: Path = BASELINE) -> dict:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    baseline = from_eval(payload, source=eval_path.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    return baseline
