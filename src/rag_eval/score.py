"""Deterministic answer scores. Public API: `score_case`, `aggregate`, `stability`, `missing_groups`.

`facts` is true when the answer was found and every `must` group has one option in the answer.
Groups are AND, options inside a group are OR. A number matches within 1% when it is a price-sized
figure or written with a decimal; a year and a small count have to match exactly. Other words match
after case-folding, with a trailing plural allowed. `cited` is true when one resolved evidence chunk
is among the citations. `abstain` applies only to a no-answer case and is true when the bot said it
was not found. `false_abstain` applies only to an answerable case. `pass` is facts and cited, or
abstain for a no-answer case. A score that does not apply is None.
"""

import re
import unicodedata
from dataclasses import dataclass

from src.rag.answer import ABSTAIN


@dataclass(frozen=True)
class CaseScore:
    facts: bool | None
    cited: bool | None
    abstain: bool | None
    false_abstain: bool | None
    passed: bool

    def as_dict(self) -> dict:
        return {
            "facts": self.facts, "cited": self.cited, "abstain": self.abstain,
            "false_abstain": self.false_abstain, "pass": self.passed,
        }


def score_case(case: dict, *, found: bool, answer: str, cited_ids: list[str],
               relevant: tuple[str, ...]) -> CaseScore:
    """Score one answer. `relevant` is the evidence chunk ids lint resolved."""
    if case["kind"] == "no-answer":
        abstain = not found or answer.strip() == ABSTAIN
        return CaseScore(None, None, abstain, None, abstain)
    facts = bool(found) and _facts(case.get("must") or [], answer)
    cited = any(chunk_id in cited_ids for chunk_id in relevant)
    return CaseScore(facts, cited, None, not found, facts and cited)


def aggregate(rows: list[dict]) -> dict:
    """Mean of each score. None values are skipped, so abstain does not dilute facts."""
    keys = ("pass", "facts", "cited", "abstain", "false_abstain", "judge", "grounded")
    metrics = {key: _mean([row.get(key) for row in rows]) for key in keys}
    by_kind: dict[str, dict] = {}
    for row in rows:
        bucket = by_kind.setdefault(row["kind"], {"n": 0, "pass": []})
        bucket["n"] += 1
        bucket["pass"].append(row["pass"])
    metrics["by_kind"] = {kind: {"n": bucket["n"], "pass": _mean(bucket["pass"])} for kind, bucket in by_kind.items()}
    metrics["failed"] = [row["id"] for row in rows if not row["pass"]]
    return metrics


def stability(runs: list[list[bool]], ids: list[str]) -> dict:
    """`pass_at_1` is the mean per-case pass rate. `pass_all` passed every repeat. `flaky` passed sometimes."""
    if not ids:
        return {"pass_at_1": 0.0, "pass_all": 0.0, "flaky": []}
    rates: list[float] = []
    flaky: list[str] = []
    always = 0
    for index, case_id in enumerate(ids):
        rate = sum(run[index] for run in runs) / len(runs)
        rates.append(rate)
        if rate == 1:
            always += 1
        elif rate > 0:
            flaky.append(case_id)
    return {"pass_at_1": sum(rates) / len(rates), "pass_all": always / len(ids), "flaky": flaky}


def norm(text: str) -> str:
    """Case-folded text with punctuation and thousands separators removed."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("\u00a0", " ").replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"\.(?!\d)", " ", text)
    text = re.sub(r"[^0-9a-z.\-]+", " ", text).replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def missing_groups(groups: list, answer: str) -> list[list[str]]:
    """`must` groups with no option in the answer. Empty when every group hits."""
    folded = norm(answer)
    return [list(group) for group in groups if not any(_option(option, folded) for option in group)]


def _facts(groups: list, answer: str) -> bool:
    return not missing_groups(groups, answer)


def _option(option: str, folded_answer: str) -> bool:
    folded = norm(option)
    if folded and folded in folded_answer:
        return True
    tokens = folded.split()
    answer_tokens = folded_answer.split()
    return bool(tokens) and all(_token(token, answer_tokens) for token in tokens)


def _token(token: str, answer_tokens: list[str]) -> bool:
    for other in answer_tokens:
        if token == other or _close(token, other):
            return True
        if len(token) >= 4 and len(other) >= 4 and _stem(token) == _stem(other):
            return True
    return False


def _stem(token: str) -> str:
    """Fold a trailing plural so story matches stories and acre matches acres."""
    if len(token) >= 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) >= 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _close(option: str, answer: str) -> bool:
    if not re.fullmatch(r"\d+(?:\.\d+)?", option) or not re.fullmatch(r"\d+(?:\.\d+)?", answer):
        return False
    left, right = float(option), float(answer)
    if left == right:
        return True
    if left == 0 or (re.fullmatch(r"\d{4}", option) and 1900 <= int(option) <= 2099):
        return False
    if "." not in option and abs(left) < 100:
        return False
    return abs(left - right) <= abs(left) * 0.01 + 1e-6


def _mean(values: list) -> float | None:
    kept = [float(value) for value in values if value is not None]
    return sum(kept) / len(kept) if kept else None
