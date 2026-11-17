"""Quality, tokens and cost at several retrieval depths. Public API: `summarize`, `format_table`, `sweep`.

The same questions are answered at k = 3, 5 and 10. The context budget is raised so a chunk is left
out because it is past k, not because the usual 2500-token cap filled up. The table is written to
`RAG_REPORT.md`. Each k also keeps its own `output/eval-sweep-k<N>-<timestamp>.json`.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.rag.config import OUTPUT_DIR, ROOT
from src.rag.llm_rag import PROMPT_VERSION

KS = (3, 5, 10)
SWEEP_BUDGET = 8000
REPORT = ROOT / "RAG_REPORT.md"


def summarize(payload: dict) -> dict:
    """One row of the sweep from an eval payload."""
    metrics = payload.get("metrics") or {}
    cost = payload.get("cost") or {}
    recall = _recall(payload)
    return {
        "k": payload.get("k"),
        "recall": recall,
        "pass": metrics.get("pass"),
        "facts": metrics.get("facts"),
        "cited": metrics.get("cited"),
        "abstain": metrics.get("abstain"),
        "false_abstain": metrics.get("false_abstain"),
        "judge": metrics.get("judge"),
        "grounded": metrics.get("grounded"),
        "answer_tokens": cost.get("answer_tokens"),
        "answer_per_1000": cost.get("answer_per_1000_usd"),
        "judge_per_1000": cost.get("judge_per_1000_usd"),
    }


def format_table(rows: list[dict]) -> str:
    """A markdown table. Rows are ordered by k. Numbers use a fixed width so a rerun of the same scores matches."""
    ordered = sorted(rows, key=lambda row: row["k"])
    columns = (
        ("k", lambda row: str(row["k"])),
        ("recall", lambda row: _n(row["recall"])),
        ("pass", lambda row: _n(row["pass"])),
        ("facts", lambda row: _n(row["facts"])),
        ("cited", lambda row: _n(row["cited"])),
        ("abstain", lambda row: _n(row["abstain"])),
        ("false abstain", lambda row: _n(row["false_abstain"])),
        ("judge", lambda row: _n(row["judge"])),
        ("grounded", lambda row: _n(row["grounded"])),
        ("tokens", lambda row: _tokens(row["answer_tokens"])),
        ("answer $ / 1000", lambda row: _money(row["answer_per_1000"])),
        ("judge $ / 1000", lambda row: _money(row["judge_per_1000"])),
    )
    header = "| " + " | ".join(name for name, _ in columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(render(row) for _, render in columns) + " |" for row in ordered]
    lines = [
        "# RAG report",
        "",
        "## k-sweep",
        "",
        f"Prompt {PROMPT_VERSION}, rerank, the same questions at each k. Context budget {SWEEP_BUDGET} tokens, "
        "so the cutoff is the number of chunks.",
        "",
        header,
        rule,
        *body,
        "",
    ]
    return "\n".join(lines)


def sweep(ks: tuple[int, ...] = KS, *, report_path: Path = REPORT, log=print) -> int:
    """Run one eval per k and write the table. A gate failure on a single k does not stop the sweep."""
    from src.rag.config import IndexPaths
    from src.rag.retrieve import load_retriever
    from src.rag_eval.run import _answer, run

    paths = IndexPaths()
    if not paths.index.exists():
        log(f"{paths.index} not found. Run `python main.py index` first.")
        return 1
    retriever = load_retriever(paths, log=lambda _: None)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows: list[dict] = []
    for k in ks:
        log(f"k-sweep: k={k}")
        eval_path = OUTPUT_DIR / f"eval-sweep-k{k}-{stamp}.json"
        report = OUTPUT_DIR / f"report-sweep-k{k}-{stamp}.md"
        answer = _answer(retriever, "rerank", k, OUTPUT_DIR / f"answers-sweep-k{k}-{stamp}.jsonl", log, SWEEP_BUDGET)
        run(k=k, search=retriever.search, answer=answer, eval_path=eval_path, report_path=report, log=log)
        rows.append(summarize(json.loads(eval_path.read_text(encoding="utf-8"))))
    text = format_table(rows)
    report_path.write_text(text, encoding="utf-8")
    log(text)
    log(f"Report: {report_path}")
    return 0


def _recall(payload: dict) -> float | None:
    k_name = payload.get("config") or "rerank"
    for row in (payload.get("retrieval") or {}).get("configs") or []:
        if row.get("config") == k_name:
            return row.get("recall")
    metrics = payload.get("metrics") or {}
    value = metrics.get("recall@5")
    return value if isinstance(value, (int, float)) else None


def _n(value) -> str:
    return "n/a" if not isinstance(value, (int, float)) else f"{value:.2f}"


def _tokens(value) -> str:
    return "n/a" if not isinstance(value, (int, float)) else str(int(value))


def _money(value) -> str:
    return "n/a" if not isinstance(value, (int, float)) else f"{value:.2f}"
