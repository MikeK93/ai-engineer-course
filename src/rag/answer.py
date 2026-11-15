"""Question -> answer with checked citations. Public API: `answer_question`, `ABSTAIN`.

Order: retrieve, pack the context, call the model, then check citations. No hits, or nothing that fits
the budget, returns `ABSTAIN` without a model call. A `found` answer with no citation that matches a
packed source also becomes `ABSTAIN`: an answer we cannot point at is not an answer.

Each question is appended to `log_path` (JSONL): the query, the retrieved ids, the ids that fit in the
context, the cited ids, the labels that were dropped, tokens, cost and latency.
"""

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import CONTEXT_BUDGET, K, OUTPUT_DIR, RAG_MODEL
from .context import pack_context
from .index import Filters
from .llm_rag import Completion, complete_rag

ABSTAIN = "Not in the documents."

_LABEL = re.compile(r"[sS]0*(\d+)")
Log = Callable[[str], None]


@dataclass(frozen=True)
class Citation:
    label: str
    chunk_id: str
    source: str
    section: str
    as_of: str
    page_start: int
    page_end: int


@dataclass
class AnswerResult:
    query: str
    found: bool
    answer: str
    citations: list[Citation] = field(default_factory=list)
    retrieved_ids: list[str] = field(default_factory=list)
    context_ids: list[str] = field(default_factory=list)
    cited_ids: list[str] = field(default_factory=list)
    invalid_labels: list[str] = field(default_factory=list)
    config: str = "rerank"
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0

    def to_log(self) -> dict:
        row = asdict(self)
        row["citations"] = [asdict(c) for c in self.citations]
        return row


def answer_question(
    question: str,
    *,
    retriever=None,
    hits: list | None = None,
    complete: Callable[[str, str], Completion] = complete_rag,
    config: str = "rerank",
    filters: Filters = Filters(),
    k: int = K,
    budget: int = CONTEXT_BUDGET,
    log_path: Path | None = None,
    log: Log = lambda _: None,
) -> AnswerResult:
    """Answer one question. Pass `hits` to skip retrieval (tests); otherwise `retriever` is required."""
    if hits is None:
        if retriever is None:
            raise ValueError("answer_question needs a retriever or hits")
        hits = retriever.search(question, config, filters=filters, k=k)
    retrieved = [h.chunk["chunk_id"] for h in hits]
    log(f"ask: {len(hits)} hits from {config}")

    packed = pack_context(hits, budget=budget)
    log(f"ask: {len(packed.labels)} sources in context ({packed.n_tokens} tokens), "
        f"{len(packed.skipped)} skipped for the budget")
    base = AnswerResult(query=question, found=False, answer=ABSTAIN, retrieved_ids=retrieved,
                        context_ids=[c["chunk_id"] for c in packed.labels.values()], config=config, model=RAG_MODEL)
    if not packed.labels:
        log("ask: nothing to send, abstaining without a model call")
        _write(log_path, base)
        return base

    log("ask: calling the model")
    done = complete(question, packed.text)
    valid, invalid = _labels(done.citations, packed.labels)
    result = AnswerResult(
        query=question, found=done.found and bool(valid),
        answer=done.answer if done.found and valid else ABSTAIN,
        citations=[_cite(label, packed.labels[label]) for label in valid] if done.found else [],
        retrieved_ids=retrieved, context_ids=base.context_ids,
        cited_ids=[packed.labels[label]["chunk_id"] for label in valid] if done.found else [],
        invalid_labels=invalid, config=config, model=RAG_MODEL,
        prompt_tokens=done.prompt_tokens, completion_tokens=done.completion_tokens,
        cost_usd=done.cost_usd, latency_s=done.latency_s,
    )
    if not result.found:
        log("ask: model gave no usable citation, answer replaced with the abstain sentence"
            if done.found else "ask: model abstained")
    _write(log_path, result)
    return result


def answers_path(now: datetime | None = None) -> Path:
    """A new log file per run: output/answers-<UTC timestamp>.jsonl."""
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUTPUT_DIR / f"answers-{stamp}.jsonl"


def _labels(raw: list[str], known: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Citations normalised to `S1` form. Unknown labels are dropped, duplicates collapse, order stays."""
    valid: list[str] = []
    invalid: list[str] = []
    for item in raw:
        for part in re.split(r"[\s,;]+", item.strip()):
            part = part.strip("[]().,")
            if not part:
                continue
            match = _LABEL.fullmatch(part)
            label = f"S{int(match.group(1))}" if match else None
            if label in known and label not in valid:
                valid.append(label)
            elif label not in known:
                invalid.append(part)
    return valid, invalid


def _cite(label: str, chunk: dict) -> Citation:
    return Citation(label, chunk["chunk_id"], chunk["source"], chunk["section"], str(chunk["as_of"]),
                    chunk["page_start"], chunk["page_end"])


def _write(path: Path | None, result: AnswerResult) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(result.to_log(), ensure_ascii=False) + "\n")
