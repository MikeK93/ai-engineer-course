"""Parsing a rag-eval report into one table row. No model calls."""

from src.rag_eval.aggregate import format_runs, label_for, parse_report, splice

REPORT = """# RAG eval v3

| metric | value |
|---|---|
| recall@5 | 0.96 |
| pass | 0.76 |
| facts | 0.76 |
| cited | 0.96 |
| abstain | 1.00 |
| false_abstain | 0.00 |
| judge | 0.86 |
| grounded | 1.00 |

Answers: 81155 tokens, $0.0405, $1.3971 per 1000 questions.
Stability: pass@1 0.76, pass-all 0.76, flaky none.

## Gate

baseline: facts 0.76 fell below 0.81
regression: s04
"""


def test_parse_report_keeps_the_metrics_and_the_gate():
    row = parse_report("report-v3-20261117T155837Z.md", REPORT)
    assert row["run"] == "v3 2026-11-17 15:58"
    assert row["abstain"] == "1.00" and row["answer_per_1000"] == "1.3971"
    assert row["flaky"] == "none"
    assert row["gate"] == "baseline: facts 0.76 fell below 0.81; regression: s04"
    assert label_for("report-v2.md") == "v2"


def test_format_runs_is_a_table_in_file_order():
    text = format_runs([
        parse_report("report-v2.md", REPORT.replace("v3", "v2")),
        parse_report("report-v3-20261117T155837Z.md", REPORT),
    ])
    assert text.startswith("## Eval runs")
    assert text.index("| v2 |") < text.index("| v3 2026-11-17 15:58 |")
    assert "report-v" not in text


def test_unstamped_reports_sort_before_stamped_ones():
    from src.rag_eval.aggregate import sort_names
    names = [
        "report-v3-20261117T155837Z.md",
        "report-v2.md",
        "report-v2-20261117T110607Z.md",
        "report-v2-20261115T205338Z.md",
    ]
    assert sort_names(names) == [
        "report-v2.md",
        "report-v2-20261115T205338Z.md",
        "report-v2-20261117T110607Z.md",
        "report-v3-20261117T155837Z.md",
    ]
    original = "# RAG report\n\n## k-sweep\n\nkept\n\n## Eval runs\n\nold\n"
    updated = splice(original, "## Eval runs\n\nnew\n")
    assert "## k-sweep" in updated and "kept" in updated
    assert "old" not in updated and "new" in updated
