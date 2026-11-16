"""Run the answer eval. Public API: `run`.

Lints the test set, scores retrieval, answers every case, then scores facts, citations, abstain,
correctness, and groundedness. `--repeat N` answers the set N times. The report is
`output/report-<prompt>-<timestamp>.md` and `output/eval-<prompt>-<timestamp>.json`. Cost per 1000 questions
is the measured token cost of this run, scaled. The gate exits 1 on a floor miss, a baseline drop,
or a per-case regression. The report is written either way.
"""

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from src.rag.answer import AnswerResult, answer_question, answers_path
from src.rag.config import EVALS_DIR, K, OUTPUT_DIR, IndexPaths
from src.rag.index import Filters
from src.rag.llm_rag import PROMPT_VERSION
from src.rag.store import read_jsonl
from src.rag_eval.gate import gate
from src.rag_eval.judge import Judgement, judge_correct, judge_grounded
from src.rag_eval.lint import TESTSET, lint
from src.rag_eval.retrieval_eval import evaluate, format_report
from src.rag_eval.score import aggregate, score_case, stability

BASELINE = EVALS_DIR / "baseline.json"


def cost_per_1000(cost_usd: float, n: int) -> float:
    """Measured cost of `n` questions, scaled to 1000."""
    return cost_usd / n * 1000 if n else 0.0


def run(repeat: int = 1, k: int = K, config: str = "rerank", *, testset: Path = TESTSET,
        chunks_path: Path | None = None, paths: IndexPaths | None = None, search=None, answer=None,
        correct: Callable = judge_correct, grounded: Callable = judge_grounded,
        report_path: Path | None = None, eval_path: Path | None = None,
        baseline_path: Path = BASELINE, log: Callable[[str], None] = print) -> int:
    """Answer the test set and write the report. Returns 1 when lint or the gate fails."""
    paths = paths or IndexPaths()
    cases = json.loads(testset.read_text(encoding="utf-8"))
    chunks = read_jsonl(chunks_path or paths.chunks)
    checked = lint(cases, chunks)
    if not checked.ok:
        for error in checked.errors:
            log(error)
        log(f"rag-eval: test set failed lint ({len(checked.errors)} errors)")
        return 1
    texts = {chunk["chunk_id"]: chunk.get("text") or "" for chunk in chunks if chunk.get("chunk_id")}
    if answer is None or search is None:
        if not paths.index.exists():
            log(f"{paths.index} not found. Run `python main.py index` first.")
            return 1
        from src.rag.retrieve import load_retriever

        retriever = load_retriever(paths, log=lambda _: None)
        search = search or retriever.search
        answer = answer or _answer(retriever, config, k, answers_path(), log)

    retrieval = evaluate(cases, checked.chunk_ids, search, k=k, log=log)
    log(format_report(retrieval))
    runs: list[list[dict]] = []
    for number in range(1, repeat + 1):
        log(f"rag-eval: repeat {number}/{repeat}, prompt {PROMPT_VERSION}")
        runs.append(_once(cases, checked.chunk_ids, texts, answer, correct, grounded, log))

    metrics = _metrics(runs, _recall(retrieval, config))
    steady = stability([[bool(row["pass"]) for row in rows] for rows in runs], [case["id"] for case in cases])
    spent = _spend(runs)
    questions = len(cases) * repeat
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
    failures = gate(metrics, baseline=baseline, passed={row["id"] for row in runs[-1] if row["pass"]})

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = report_path or OUTPUT_DIR / f"report-{PROMPT_VERSION}-{stamp}.md"
    payload = eval_path or OUTPUT_DIR / f"eval-{PROMPT_VERSION}-{stamp}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = _markdown(metrics, steady, spent, questions, retrieval, runs[-1], failures)
    report.write_text(body, encoding="utf-8")
    payload.write_text(json.dumps({
        "prompt": PROMPT_VERSION, "repeat": repeat, "k": k, "config": config,
        "metrics": metrics, "stability": steady, "cost": _cost_block(spent, questions),
        "retrieval": retrieval.to_dict(), "cases": runs[-1], "gate": failures,
    }, indent=2), encoding="utf-8")
    log(body)
    log(f"Report: {report}")
    log(f"Log: {payload}")
    if failures:
        log(f"rag-eval: gate failed ({len(failures)})")
        return 1
    log("rag-eval: gate passed")
    return 0


def _answer(retriever, config: str, k: int, log_path: Path, log):
    def answer(case: dict) -> AnswerResult:
        return answer_question(
            case["question"], retriever=retriever, config=config, filters=_filters(case), k=k,
            log_path=log_path, log=log,
        )
    return answer


def _once(cases, relevant, texts, answer, correct, grounded, log) -> list[dict]:
    rows: list[dict] = []
    for case in cases:
        log(f"rag-eval: {case['id']} {case['kind']}")
        result = answer(case)
        scored = score_case(case, found=result.found, answer=result.answer, cited_ids=result.cited_ids,
                            relevant=relevant.get(case["id"], ()))
        sources = _sources(result, texts)
        judged = _safe(correct, (case["question"], case["reference"], result.answer), log, case["id"], "correct")
        support = _safe(grounded, (result.answer, result.found, sources), log, case["id"], "grounded")
        row = {
            "id": case["id"], "kind": case["kind"], "question": case["question"],
            "reference": case["reference"], "answer": result.answer, "found": result.found,
            "cited_ids": list(result.cited_ids), "relevant": list(relevant.get(case["id"], ())),
            "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
            "cost_usd": result.cost_usd,
            "judge": judged.passed, "judge_reason": judged.reason,
            "grounded": support.passed, "grounded_reason": support.reason,
            "unsupported": list(support.unsupported),
            "judge_prompt_tokens": judged.prompt_tokens + support.prompt_tokens,
            "judge_completion_tokens": judged.completion_tokens + support.completion_tokens,
            "judge_cost_usd": judged.cost_usd + support.cost_usd,
        }
        row.update(scored.as_dict())
        rows.append(row)
        log(f"rag-eval: {case['id']} pass={row['pass']} judge={row['judge']} grounded={row['grounded']}")
    return rows


def _safe(fn, args, log, case_id, name) -> Judgement:
    try:
        return fn(*args)
    except Exception as exc:
        log(f"rag-eval: {case_id} {name} failed: {exc}")
        return Judgement(False, str(exc), (), 0, 0, 0.0)


def _sources(result: AnswerResult, texts: dict[str, str]) -> list[tuple[str, str]]:
    blocks = []
    for citation in result.citations:
        header = f"{citation.label} {citation.source} · {citation.section} · {citation.as_of}"
        blocks.append((header, texts.get(citation.chunk_id, "")))
    return blocks


def _metrics(runs: list[list[dict]], recall: float) -> dict:
    parts = [aggregate(rows) for rows in runs]
    keys = ("pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded")
    metrics = {key: _mean([part[key] for part in parts]) for key in keys}
    metrics["recall@5"] = recall
    metrics["by_kind"] = parts[-1]["by_kind"]
    metrics["failed"] = parts[-1]["failed"]
    return metrics


def _recall(retrieval, config: str) -> float:
    for row in retrieval.configs:
        if row.config == config:
            return row.score.recall
    return retrieval.configs[-1].score.recall


def _spend(runs: list[list[dict]]) -> dict:
    return {
        "answer_cost": sum(row["cost_usd"] for rows in runs for row in rows),
        "answer_tokens": sum(row["prompt_tokens"] + row["completion_tokens"] for rows in runs for row in rows),
        "judge_cost": sum(row["judge_cost_usd"] for rows in runs for row in rows),
        "judge_tokens": sum(row["judge_prompt_tokens"] + row["judge_completion_tokens"] for rows in runs for row in rows),
    }


def _cost_block(spent: dict, questions: int) -> dict:
    return {
        "questions": questions,
        "answer_tokens": spent["answer_tokens"],
        "answer_cost_usd": spent["answer_cost"],
        "answer_per_1000_usd": cost_per_1000(spent["answer_cost"], questions),
        "judge_tokens": spent["judge_tokens"],
        "judge_cost_usd": spent["judge_cost"],
        "judge_per_1000_usd": cost_per_1000(spent["judge_cost"], questions),
    }


def _markdown(metrics, steady, spent, questions, retrieval, rows, failures) -> str:
    cost = _cost_block(spent, questions)
    lines = [
        f"# RAG eval {PROMPT_VERSION}",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    for key in ("recall@5", "pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded"):
        lines.append(f"| {key} | {_num(metrics.get(key))} |")
    lines += [
        "",
        f"Answers: {cost['answer_tokens']} tokens, ${cost['answer_cost_usd']:.4f}, "
        f"${cost['answer_per_1000_usd']:.4f} per 1000 questions.",
        f"Judge: {cost['judge_tokens']} tokens, ${cost['judge_cost_usd']:.4f}, "
        f"${cost['judge_per_1000_usd']:.4f} per 1000 questions.",
        f"Stability: pass@1 {_num(steady['pass_at_1'])}, pass-all {_num(steady['pass_all'])}, "
        f"flaky {', '.join(steady['flaky']) or 'none'}.",
        "",
        "## By kind",
        "",
        "| kind | n | pass |",
        "|---|---|---|",
    ]
    for kind, bucket in metrics["by_kind"].items():
        lines.append(f"| {kind} | {bucket['n']} | {_num(bucket['pass'])} |")
    lines += ["", "## Retrieval", "", format_report(retrieval), "", "## Cases", "",
              "| id | kind | pass | facts | cited | judge | grounded |",
              "|---|---|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['kind']} | {_mark(row['pass'])} | {_mark(row['facts'])} | "
            f"{_mark(row['cited'])} | {_mark(row['judge'])} | {_mark(row['grounded'])} |"
        )
    lines += ["", "## Worth reading", ""]
    shown = [row for row in rows if row["pass"] is False or row["judge"] is False or row["grounded"] is False]
    if not shown:
        lines.append("None.")
    for row in shown:
        lines += [
            f"### {row['id']}",
            "",
            f"Question: {row['question']}",
            "",
            f"Reference: {row['reference']}",
            "",
            f"Answer: {row['answer']}",
            "",
            f"Cited: {', '.join(row['cited_ids']) or 'none'}",
            "",
            f"Judge: {row['judge_reason'] or 'none'}",
            "",
        ]
        if row["unsupported"]:
            lines.append("Unsupported: " + "; ".join(row["unsupported"]))
            lines.append("")
    lines += ["## Gate", ""]
    lines.append("\n".join(failures) if failures else "Passed.")
    lines.append("")
    return "\n".join(lines)


def _filters(case: dict) -> Filters:
    doc_type = case.get("doc_type")
    if doc_type is None:
        return Filters()
    types = (doc_type,) if isinstance(doc_type, str) else tuple(doc_type)
    return Filters(doc_types=types)


def _mean(values: list) -> float | None:
    kept = [value for value in values if isinstance(value, (int, float))]
    return sum(kept) / len(kept) if kept else None


def _num(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _mark(value) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"
