"""Retrieval metrics. A fake search stands in for the index, so nothing is downloaded."""

from types import SimpleNamespace

from src.rag.index import Filters
from src.rag.retrieve import CONFIGS
from src.rag_eval.retrieval_eval import evaluate, format_report, score


def hit(chunk_id):
    return SimpleNamespace(chunk={"chunk_id": chunk_id})


def test_ranks_two_one_and_missing_are_recall_0_67_and_mrr_0_50():
    rows = [
        ("a", ("A",), ("x", "A")),
        ("b", ("B",), ("B", "x")),
        ("c", ("C",), ("x", "y", "z")),
    ]
    result = score(rows, k=5)
    assert round(result.recall, 2) == 0.67
    assert round(result.mrr, 2) == 0.50
    assert result.misses == ("c",)
    assert result.missing == (("c", ("C",)),)


def test_a_hit_past_k_is_a_miss_and_a_partial_multi_chunk_is_a_fraction():
    past = score([("q", ("A",), ("v", "w", "x", "y", "z", "A"))], k=5)
    assert past.recall == 0.0 and past.mrr == 0.0 and past.misses == ("q",)

    partial = score([("m", ("A", "B"), ("A", "x"))], k=5)
    assert partial.recall == 0.5 and partial.mrr == 1.0
    assert partial.misses == ("m",) and partial.missing == (("m", ("B",)),)


def test_evaluate_skips_no_answer_and_passes_the_case_filter():
    calls = []

    def search(query, config, *, filters, k):
        calls.append((query, config, filters, k))
        found = {"vector": ["x", "gold"], "bm25": ["gold"], "hybrid": ["gold"], "rerank": ["nope"]}
        return [hit(chunk_id) for chunk_id in found[config]]

    clock = iter([0.0, 0.025, 10.0, 10.01, 20.0, 20.0, 30.0, 30.05]).__next__
    cases = [
        {"id": "e01", "kind": "exact", "question": "What is the price?"},
        {"id": "n01", "kind": "no-answer", "question": "Who owns the moon?"},
        {"id": "f01", "kind": "fund-vs-listing", "question": "What is the fee?", "doc_type": "fund_om"},
    ]
    relevant = {"e01": ("gold",), "n01": (), "f01": ("gold",)}
    report = evaluate(cases, relevant, search, k=5, clock=clock, log=lambda _: None)

    assert [row.config for row in report.configs] == list(CONFIGS)
    assert all(call[3] == 5 for call in calls)
    assert {call[0] for call in calls} == {"What is the price?", "What is the fee?"}
    fund = [call for call in calls if call[0] == "What is the fee?"]
    assert fund and all(call[2] == Filters(doc_types=("fund_om",)) for call in fund)
    bare = [call for call in calls if call[0] == "What is the price?"]
    assert all(call[2] == Filters() for call in bare)

    by_config = {row.config: row for row in report.configs}
    assert round(by_config["vector"].score.recall, 2) == 1.00
    assert by_config["vector"].score.mrr == 0.5
    assert by_config["vector"].ms_per_query == 12.5
    assert by_config["rerank"].score.misses == ("e01", "f01")
    text = format_report(report)
    assert text.startswith("| config | recall@5 | MRR | ms/query | miss |")
    assert "| rerank | 0.00 | 0.00 | 25.0 | e01, f01 |" in text
    assert "| config | id | missing |" in text
    assert "| rerank | e01 | gold |" in text
