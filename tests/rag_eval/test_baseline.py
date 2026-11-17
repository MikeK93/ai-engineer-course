"""Baseline construction from a repeated eval. No model calls."""

from src.rag_eval.baseline import from_eval


def test_passed_excludes_the_last_run_failures_and_the_flaky_ids():
    payload = {
        "prompt": "v2", "repeat": 3, "k": 5,
        "metrics": {"pass": 0.7, "facts": 0.8, "false_abstain": 0.01, "by_kind": {}, "failed": ["a"]},
        "stability": {"flaky": ["b"], "pass_at_1": 0.7, "pass_all": 0.5},
        "cases": [
            {"id": "a", "pass": False},
            {"id": "b", "pass": True},
            {"id": "c", "pass": True},
        ],
    }
    baseline = from_eval(payload, source="eval.json")
    assert baseline["passed"] == ["c"]
    assert baseline["flaky"] == ["b"]
    assert baseline["metrics"] == {"pass": 0.7, "facts": 0.8, "false_abstain": 0.01}
    assert baseline["repeat"] == 3
