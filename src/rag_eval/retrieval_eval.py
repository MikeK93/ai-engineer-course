"""Retrieval metrics. Public API: `score`, `evaluate`, `format_report`, `run`.

`score` is the whole metric. It sees question id, the relevant chunk ids, and the ranked ids,
and nothing about Qdrant or the models. recall@k is the mean, over questions, of the share of
relevant ids that landed in the top k. MRR is the mean of 1/rank of the first relevant id, and 0
when none of them did. A miss is a question that is missing at least one relevant id. Ranks 2, 1
and missing are recall 0.67 and MRR 0.50.

`evaluate` asks an injected search for each config and times it. No-answer cases have no relevant
ids and are not searched. A case `doc_type` becomes the same `Filters` search already uses.
`run` lints first, then searches the built index. It does not call the answer model.
"""

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.rag.config import K, OUTPUT_DIR, IndexPaths
from src.rag.index import Filters
from src.rag.retrieve import CONFIGS
from src.rag.store import read_jsonl
from src.rag_eval.lint import TESTSET, lint

Search = Callable[..., list]


@dataclass(frozen=True)
class RetrievalScore:
    recall: float
    mrr: float
    misses: tuple[str, ...]
    missing: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class ConfigResult:
    config: str
    n: int
    score: RetrievalScore
    ms_per_query: float


@dataclass(frozen=True)
class RetrievalReport:
    k: int
    configs: tuple[ConfigResult, ...]

    def to_dict(self) -> dict:
        return {
            "k": self.k,
            "configs": [
                {
                    "config": row.config,
                    "n": row.n,
                    "recall": row.score.recall,
                    "mrr": row.score.mrr,
                    "ms_per_query": row.ms_per_query,
                    "misses": list(row.score.misses),
                    "missing": {case_id: list(ids) for case_id, ids in row.score.missing},
                }
                for row in self.configs
            ],
        }


def score(rows: Sequence[tuple[str, Sequence[str], Sequence[str]]], *, k: int) -> RetrievalScore:
    """`(question id, relevant chunk ids, ranked chunk ids)` in rank order."""
    recalls: list[float] = []
    reciprocal: list[float] = []
    misses: list[str] = []
    missing: list[tuple[str, tuple[str, ...]]] = []
    for case_id, relevant, ranked in rows:
        wanted = _unique(relevant)
        if not wanted:
            continue
        top = set(list(ranked)[:k])
        found = [chunk_id for chunk_id in wanted if chunk_id in top]
        recalls.append(len(found) / len(wanted))
        reciprocal.append(_reciprocal(wanted, ranked, k))
        if len(found) < len(wanted):
            misses.append(case_id)
            missing.append((case_id, tuple(chunk_id for chunk_id in wanted if chunk_id not in top)))
    n = len(recalls)
    return RetrievalScore(
        recall=sum(recalls) / n if n else 0.0,
        mrr=sum(reciprocal) / n if n else 0.0,
        misses=tuple(misses),
        missing=tuple(missing),
    )


def evaluate(cases: list[dict], relevant: dict[str, tuple[str, ...]], search: Search, *,
             k: int = K, configs: Sequence[str] = CONFIGS,
             clock: Callable[[], float] = time.perf_counter,
             log: Callable[[str], None] = lambda _: None) -> RetrievalReport:
    """Search each answerable case under every config. `search` is `Retriever.search`."""
    picked = [(case, relevant[case["id"]]) for case in cases if relevant.get(case["id"])]
    log(f"eval-retrieval: {len(picked)} answerable questions, k={k}")
    rows: list[ConfigResult] = []
    for config in configs:
        log(f"eval-retrieval: {config}")
        rankings: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        started = clock()
        for case, ids in picked:
            hits = search(case["question"], config, filters=_filters(case), k=k)
            rankings.append((case["id"], ids, tuple(hit.chunk["chunk_id"] for hit in hits)))
        elapsed_ms = (clock() - started) * 1000
        rows.append(ConfigResult(config, len(picked), score(rankings, k=k), elapsed_ms / len(picked) if picked else 0.0))
    return RetrievalReport(k, tuple(rows))


def _table(columns: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join((header, rule, *body))


def format_report(report: RetrievalReport) -> str:
    """Two markdown tables: one row per config, then one row per missing evidence chunk."""
    metrics = []
    gaps = []
    for row in report.configs:
        shown = ", ".join(row.score.misses) if row.score.misses else "none"
        metrics.append((row.config, f"{row.score.recall:.2f}", f"{row.score.mrr:.2f}", f"{row.ms_per_query:.1f}", shown))
        for case_id, ids in row.score.missing:
            gaps.append((row.config, case_id, ", ".join(ids)))
    parts = [_table(("config", f"recall@{report.k}", "MRR", "ms/query", "miss"), metrics)]
    if gaps:
        parts.append(_table(("config", "id", "missing"), gaps))
    return "\n\n".join(parts)


def retrieval_path(now: datetime | None = None) -> Path:
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUTPUT_DIR / f"retrieval-{stamp}.json"


def run(k: int = K, *, testset: Path = TESTSET, chunks_path: Path | None = None,
        paths: IndexPaths | None = None, search: Search | None = None,
        log_path: Path | None = None, log: Callable[[str], None] = print) -> int:
    """Lint, score the four configs, print the table, write `output/retrieval-<timestamp>.json`."""
    paths = paths or IndexPaths()
    cases = json.loads(testset.read_text(encoding="utf-8"))
    result = lint(cases, read_jsonl(chunks_path or paths.chunks))
    if not result.ok:
        for error in result.errors:
            log(error)
        log(f"eval-retrieval: test set failed lint ({len(result.errors)} errors)")
        return 1
    retriever = None
    if search is None:
        if not paths.index.exists():
            log(f"{paths.index} not found. Run `python main.py index` first.")
            return 1
        from src.rag.retrieve import load_retriever

        retriever = load_retriever(paths, log=lambda _: None)
        search = retriever.search
    try:
        report = evaluate(cases, result.chunk_ids, search, k=k, log=log)
        log(format_report(report))
        path = log_path or retrieval_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        log(f"Log: {path}")
        return 0
    finally:
        if retriever is not None:
            retriever.close()


def _filters(case: dict) -> Filters:
    doc_type = case.get("doc_type")
    if doc_type is None:
        return Filters()
    types = (doc_type,) if isinstance(doc_type, str) else tuple(doc_type)
    return Filters(doc_types=types)


def _unique(ids: Sequence[str]) -> list[str]:
    seen: list[str] = []
    for chunk_id in ids:
        if chunk_id not in seen:
            seen.append(chunk_id)
    return seen


def _reciprocal(wanted: Sequence[str], ranked: Sequence[str], k: int) -> float:
    needed = set(wanted)
    for rank, chunk_id in enumerate(list(ranked)[:k], start=1):
        if chunk_id in needed:
            return 1.0 / rank
    return 0.0
