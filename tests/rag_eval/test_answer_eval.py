"""Answer scoring, judge, gate, and the eval run. Fakes stand in for the models."""

import json
from types import SimpleNamespace

from src.rag.answer import ABSTAIN, AnswerResult
from src.rag_eval.gate import gate
from src.rag_eval.judge import Claims, Judgement, Verdict, judge_correct, judge_grounded
from src.rag_eval.run import cost_per_1000, run
from src.rag_eval.score import aggregate, score_case, stability


def _case(kind="exact", must=None):
    return {"id": "e1", "kind": kind, "must": must if must is not None else [["$1,189,900"]]}


def test_facts_accept_a_price_within_one_percent_and_a_plural():
    hit = score_case(_case(), found=True, answer="The asking price is 1,250,000.", cited_ids=["d#0"],
                     relevant=("d#0",))
    assert hit.facts is False  # 1,250,000 is not within 1% of 1,189,900

    price = score_case(_case(must=[["$1,250,000"]]), found=True, answer="About $1,262,500.",
                       cited_ids=["d#0"], relevant=("d#0",))
    assert price.facts is True and price.passed is True

    over = score_case(_case(must=[["$1,250,000"]]), found=True, answer="$1,270,000",
                      cited_ids=["d#0"], relevant=("d#0",))
    assert over.facts is False

    floors = score_case(_case(must=[["20-story"]]), found=True, answer="The building is 20 stories.",
                        cited_ids=["d#0"], relevant=("d#0",))
    assert floors.facts is True
    wrong_floors = score_case(_case(must=[["20-story"]]), found=True, answer="The building is 21 stories.",
                              cited_ids=["a"], relevant=("d#0",))
    assert wrong_floors.facts is False and wrong_floors.cited is False and wrong_floors.passed is False

    year = score_case(_case(must=[["2020"]]), found=True, answer="Updated in 2021.",
                      cited_ids=["d#0"], relevant=("d#0",))
    assert year.facts is False


def test_groups_are_and_and_options_inside_are_or():
    either = score_case(_case(must=[["nope", "$1,189,900"]]), found=True, answer="It is $1,189,900.",
                        cited_ids=["d#0"], relevant=("d#0",))
    assert either.facts is True
    both = score_case(_case(must=[["$1,189,900"], ["acres"]]), found=True, answer="It is $1,189,900.",
                      cited_ids=["d#0"], relevant=("d#0",))
    assert both.facts is False
    assert score_case(_case(), found=False, answer=ABSTAIN, cited_ids=[], relevant=("d#0",)).false_abstain is True


def test_no_answer_scores_abstain_and_leaves_facts_empty():
    good = score_case({"id": "n1", "kind": "no-answer"}, found=False, answer=ABSTAIN, cited_ids=[], relevant=())
    assert good.abstain is True and good.passed is True and good.facts is None and good.cited is None
    bad = score_case({"id": "n1", "kind": "no-answer"}, found=True, answer="$1", cited_ids=["d#0"], relevant=())
    assert bad.abstain is False and bad.passed is False and bad.false_abstain is None


def test_aggregate_skips_none_and_stability_names_the_flaky_case():
    rows = [
        {"id": "e1", "kind": "exact", "pass": True, "facts": True, "cited": True, "abstain": None,
         "false_abstain": False, "judge": True, "grounded": True},
        {"id": "n1", "kind": "no-answer", "pass": True, "facts": None, "cited": None, "abstain": True,
         "false_abstain": None, "judge": True, "grounded": None},
    ]
    metrics = aggregate(rows)
    assert metrics["facts"] == 1.0 and metrics["abstain"] == 1.0 and metrics["failed"] == []
    assert metrics["by_kind"]["exact"]["n"] == 1
    steady = stability([[True, False], [True, True]], ["e1", "n1"])
    assert steady["flaky"] == ["n1"] and steady["pass_all"] == 0.5 and steady["pass_at_1"] == 0.75


def test_judge_reads_the_reference_and_an_abstain_makes_no_grounded_call():
    seen = {}

    def complete(system, user, model):
        seen["user"] = user
        seen["system"] = system
        return model(reason="the price is the same", verdict="correct"), 3, 2, 0.01

    judged = judge_correct("What is the price?", "$1,189,900", "The price is $1,189,900.", complete=complete)
    assert judged.passed is True and "Reference: $1,189,900" in seen["user"]
    assert "key fact" in seen["system"]

    def boom(*_args):
        raise AssertionError("abstain must not call the model")

    skipped = judge_grounded(ABSTAIN, False, [], complete=boom)
    assert skipped.passed is None and skipped.unsupported == ()

    def claims(system, user, model):
        return model(reason="one number", claims=[{"claim": "the fee is 2%", "supported": False}]), 1, 1, 0.0

    grounded = judge_grounded("The fee is 2%.", True, [("S1 doc · fee · 2024", "fee is 1%")], complete=claims)
    assert grounded.passed is False and grounded.unsupported == ("the fee is 2%",)


def test_gate_floors_tolerance_and_regressions():
    healthy = {"recall@5": 0.9, "pass": 0.8, "abstain": 1.0, "grounded": 0.9, "false_abstain": 0.1, "facts": 0.8}
    assert gate(healthy) == []
    assert any(line.startswith("floor: abstain") for line in gate({**healthy, "abstain": 0.5}))
    baseline = {"metrics": healthy, "passed": ["e1", "e2"]}
    held = gate({**healthy, "pass": 0.76}, baseline=baseline, passed={"e1", "e2"})
    assert held == []
    dropped = gate({**healthy, "pass": 0.7}, baseline=baseline, passed={"e1"})
    assert any(line.startswith("baseline: pass") for line in dropped)
    assert "regression: e2" in dropped
    rose = gate({**healthy, "false_abstain": 0.2}, baseline=baseline, passed={"e1", "e2"})
    assert any("false_abstain" in line for line in rose)


def test_run_writes_the_report_and_the_cost(tmp_path):
    chunk = {"chunk_id": "d#0", "doc_id": "doc", "embed_prefix": "Listing", "text": "Asking price $1,189,900"}
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text(json.dumps(chunk) + "\n", encoding="utf-8")
    cases = [
        {"id": "e1", "kind": "exact", "question": "What is the price?", "source": "doc",
         "evidence": ["$1,189,900"], "must": [["$1,189,900"]], "reference": "$1,189,900"},
        {"id": "e2", "kind": "exact", "question": "What is the asking price?", "source": "doc",
         "evidence": ["$1,189,900"], "must": [["$1,189,900"]], "reference": "$1,189,900"},
        {"id": "n1", "kind": "no-answer", "question": "Who owns the moon?", "source": None, "reference": ABSTAIN},
        {"id": "n2", "kind": "no-answer", "question": "What is the tax?", "source": None, "reference": ABSTAIN},
    ]
    testset = tmp_path / "testset.json"
    testset.write_text(json.dumps(cases), encoding="utf-8")

    def search(query, config, *, filters, k):
        return [SimpleNamespace(chunk={"chunk_id": "d#0"})]

    def answer(case):
        if case["kind"] == "no-answer":
            return AnswerResult(query=case["question"], found=False, answer=ABSTAIN)
        return AnswerResult(query=case["question"], found=True, answer="The price is $1,189,900.",
                            cited_ids=["d#0"], prompt_tokens=100, completion_tokens=20, cost_usd=0.01)

    def correct(question, reference, answer):
        return Judgement(True, "matches the reference", (), 10, 5, 0.002)

    def grounded(answer, found, sources):
        if not found:
            return Judgement(None, "", (), 0, 0, 0.0)
        return Judgement(True, "supported", (), 8, 4, 0.001)

    report = tmp_path / "report.md"
    payload = tmp_path / "eval.json"
    code = run(testset=testset, chunks_path=chunks, paths=SimpleNamespace(index=tmp_path, chunks=chunks),
               search=search, answer=answer, correct=correct, grounded=grounded,
               report_path=report, eval_path=payload, baseline_path=tmp_path / "no-baseline.json",
               log=lambda _: None)
    text = report.read_text(encoding="utf-8")
    saved = json.loads(payload.read_text(encoding="utf-8"))
    assert code == 0
    assert "e1" in text and "Passed." in text
    assert saved["metrics"]["pass"] == 1.0 and saved["metrics"]["recall@5"] == 1.0
    assert cost_per_1000(0.02, 4) == 5.0
    assert saved["cost"]["answer_per_1000_usd"] == 5.0
    assert Verdict.model_validate_json('{"reason": "because", "verdict": "correct"}').verdict == "correct"
    assert Claims(reason="split", claims=[]).claims == []
