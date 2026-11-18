"""Baseline construction from a repeated eval. No model calls."""

import json

from src.rag_eval.baseline import from_eval, metadata_path, source_metadata, write_baseline


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


def test_source_metadata_keeps_the_answer_and_drops_tokens():
    payload = {
        "prompt": "v2", "repeat": 3, "k": 5,
        "cases": [{
            "id": "s04", "kind": "similar-doc", "pass": True, "facts": True, "cited": True,
            "answer": "Yes, work not completed.", "cited_ids": ["d#2"], "must": [["Yes, work not completed"]],
            "prompt_tokens": 100, "judge_reason": "fine",
        }],
    }
    meta = source_metadata(payload, source="eval.json")
    case = meta["cases"][0]
    assert meta["source"] == "eval.json" and meta["prompt"] == "v2"
    assert case["answer"] == "Yes, work not completed." and case["cited_ids"] == ["d#2"]
    assert "prompt_tokens" not in case and "judge_reason" not in case


def test_write_baseline_writes_the_metadata_beside_the_snapshot(tmp_path):
    eval_path = tmp_path / "eval.json"
    eval_path.write_text(json.dumps({
        "prompt": "v2", "repeat": 3, "k": 5,
        "metrics": {"pass": 1.0},
        "stability": {"flaky": []},
        "cases": [{"id": "s04", "pass": True, "facts": True, "answer": "Yes, work not completed."}],
    }), encoding="utf-8")
    dest = tmp_path / "baseline.json"
    write_baseline(eval_path, dest=dest)
    meta = json.loads(metadata_path(dest).read_text(encoding="utf-8"))
    assert dest.is_file()
    assert meta["cases"][0]["id"] == "s04"
    assert meta["cases"][0]["answer"] == "Yes, work not completed."
