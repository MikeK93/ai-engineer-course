"""k-sweep table formatting. No model calls."""

from src.rag_eval.sweep import format_table, summarize


def test_summarize_reads_rerank_recall_and_cost():
    payload = {
        "k": 10, "config": "rerank",
        "metrics": {"pass": 0.8, "facts": 0.9, "cited": 1, "abstain": 1, "false_abstain": 0,
                    "judge": 0.7, "grounded": 0.95, "recall@5": 0.5},
        "retrieval": {"configs": [{"config": "rerank", "recall": 0.96}, {"config": "bm25", "recall": 0.4}]},
        "cost": {"answer_tokens": 1000, "answer_per_1000_usd": 1.5, "judge_per_1000_usd": 0.2},
    }
    row = summarize(payload)
    assert row["k"] == 10 and row["recall"] == 0.96 and row["pass"] == 0.8
    text = format_table([row])
    assert "| k | recall | pass |" in text
    assert "| 10 | 0.96 | 0.80 |" in text
