"""Compare the judge with the hand labels. Public API: `compare`, `calibrate`.

The labels grade frozen answer sentences from one eval file. This re-judges those sentences.
It does not ask the bot again, so a later chunking change cannot move the exam. A judge score
of None (an abstain has no claims) is left out of that axis. `false_pass` is the judge accepting
what you rejected. `false_fail` is the reverse.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.rag.config import EVALS_DIR, OUTPUT_DIR
from src.rag.store import read_jsonl
from src.rag_eval.judge import JUDGE_VERSION, judge_correct, judge_grounded

LABELS = EVALS_DIR / "labels.json"


@dataclass(frozen=True)
class Axis:
    name: str
    n: int
    agreement: float
    false_pass: float
    false_fail: float
    disagreements: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "n": self.n, "agreement": self.agreement, "false_pass": self.false_pass,
            "false_fail": self.false_fail, "disagreements": list(self.disagreements),
        }


def compare(rows: list[dict], *, name: str) -> Axis:
    """`rows` are `{id, human, judge}`. `judge` may be None when that axis does not apply."""
    kept = [row for row in rows if isinstance(row["judge"], bool)]
    n = len(kept)
    if not n:
        return Axis(name, 0, 0.0, 0.0, 0.0, ())
    matches = [row for row in kept if row["human"] is row["judge"]]
    false_pass = [row["id"] for row in kept if row["judge"] and not row["human"]]
    false_fail = [row["id"] for row in kept if row["human"] and not row["judge"]]
    disagreements = tuple(row["id"] for row in kept if row["human"] is not row["judge"])
    return Axis(name, n, len(matches) / n, len(false_pass) / n, len(false_fail) / n, disagreements)


def calibrate(eval_path: Path, *, labels_path: Path = LABELS, chunks_path: Path | None = None,
              correct: Callable = judge_correct, grounded: Callable = judge_grounded,
              log_path: Path | None = None, log: Callable[[str], None] = print) -> int:
    """Re-judge the labeled answers and print agreement. Returns 0."""
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    cases = {row["id"]: row for row in json.loads(eval_path.read_text(encoding="utf-8"))["cases"]}
    missing = [row["id"] for row in labels if row["id"] not in cases]
    if missing:
        log(f"calibrate: label ids not in {eval_path.name}: {', '.join(missing)}")
        return 1
    chunks = {chunk["chunk_id"]: chunk for chunk in read_jsonl(chunks_path) if chunk.get("chunk_id")} if chunks_path else {}
    if chunks_path is None:
        from src.rag.config import CHUNKS
        chunks = {chunk["chunk_id"]: chunk for chunk in read_jsonl(CHUNKS) if chunk.get("chunk_id")}

    correct_rows: list[dict] = []
    grounded_rows: list[dict] = []
    detail: list[dict] = []
    for label in labels:
        case = cases[label["id"]]
        log(f"calibrate: {label['id']}")
        verdict = correct(case["question"], case["reference"], case["answer"])
        sources = _sources(case.get("cited_ids") or [], chunks)
        support = grounded(case["answer"], bool(case.get("found")), sources)
        correct_rows.append({"id": label["id"], "human": bool(label["correct"]), "judge": verdict.passed})
        grounded_rows.append({"id": label["id"], "human": bool(label["grounded"]), "judge": support.passed})
        detail.append({
            "id": label["id"], "note": label.get("note", ""),
            "human_correct": label["correct"], "judge_correct": verdict.passed, "correct_reason": verdict.reason,
            "human_grounded": label["grounded"], "judge_grounded": support.passed, "grounded_reason": support.reason,
            "unsupported": list(support.unsupported),
        })

    axes = (compare(correct_rows, name="correct"), compare(grounded_rows, name="grounded"))
    text = _format(eval_path, axes)
    log(text)
    path = log_path or _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "eval": str(eval_path), "judge": JUDGE_VERSION,
        "correct": axes[0].as_dict(), "grounded": axes[1].as_dict(), "cases": detail,
    }, indent=2), encoding="utf-8")
    log(f"Log: {path}")
    return 0


def _sources(cited_ids: list[str], chunks: dict[str, dict]) -> list[tuple[str, str]]:
    blocks = []
    for index, chunk_id in enumerate(cited_ids, start=1):
        chunk = chunks.get(chunk_id, {})
        header = f"S{index} {chunk.get('source', '')} · {chunk.get('embed_prefix') or chunk.get('section', '')} · {chunk.get('as_of', '')}"
        blocks.append((header, chunk.get("text") or ""))
    return blocks


def _format(eval_path: Path, axes: tuple[Axis, Axis]) -> str:
    lines = [f"calibrate: {len(axes)} axes on {eval_path.name}", ""]
    lines.append(f"{'axis':<10} {'n':>4} {'agreement':>10} {'false_pass':>11} {'false_fail':>11}  disagreements")
    for axis in axes:
        shown = ", ".join(axis.disagreements) if axis.disagreements else "none"
        lines.append(
            f"{axis.name:<10} {axis.n:4d} {axis.agreement:10.2f} {axis.false_pass:11.2f} {axis.false_fail:11.2f}  {shown}"
        )
    return "\n".join(lines)


def _path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUTPUT_DIR / f"calibration-{JUDGE_VERSION}-{stamp}.json"
