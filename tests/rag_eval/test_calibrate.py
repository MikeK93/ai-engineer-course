"""Calibration math. A fake judge stands in for the model."""

import json

from src.rag_eval.calibrate import calibrate, compare
from src.rag_eval.judge import Judgement


def test_compare_counts_false_pass_and_false_fail_and_skips_abstain():
    rows = [
        {"id": "a", "human": True, "judge": True},
        {"id": "b", "human": False, "judge": True},
        {"id": "c", "human": True, "judge": False},
        {"id": "d", "human": True, "judge": None},
    ]
    axis = compare(rows, name="correct")
    assert axis.n == 3
    assert round(axis.agreement, 2) == 0.33
    assert round(axis.false_pass, 2) == 0.33
    assert round(axis.false_fail, 2) == 0.33
    assert axis.disagreements == ("b", "c")


def test_calibrate_rejudges_the_saved_answer(tmp_path):
    seen = {}

    def correct(question, reference, answer):
        seen["answer"] = answer
        return Judgement(True, "matches", (), 1, 1, 0.0)

    def grounded(answer, found, sources):
        seen["sources"] = sources
        return Judgement(False, "one claim is extra", ("extra",), 1, 1, 0.0)

    eval_path = tmp_path / "eval.json"
    eval_path.write_text(json.dumps({"cases": [{
        "id": "e04", "question": "price?", "reference": "$1", "answer": "It is $1.",
        "found": True, "cited_ids": ["d#0"],
    }]}), encoding="utf-8")
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps([{"id": "e04", "correct": True, "grounded": True, "note": "price"}]), encoding="utf-8")
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text(json.dumps({
        "chunk_id": "d#0", "source": "pdfs/x.pdf", "embed_prefix": "Title | Price", "as_of": "2024",
        "text": "Asking price $1.",
    }) + "\n", encoding="utf-8")
    log_path = tmp_path / "calibration.json"
    code = calibrate(eval_path, labels_path=labels, chunks_path=chunks, correct=correct, grounded=grounded,
                     log_path=log_path, log=lambda _: None)
    saved = json.loads(log_path.read_text(encoding="utf-8"))
    assert code == 0
    assert seen["answer"] == "It is $1."
    assert seen["sources"][0][1] == "Asking price $1."
    assert saved["correct"]["agreement"] == 1.0
    assert saved["grounded"]["disagreements"] == ["e04"]
    assert saved["grounded"]["false_fail"] == 1.0
