"""Correctness and groundedness. Public API: `judge_correct`, `judge_grounded`.

Both calls use `JUDGE_MODEL` at temperature 0. The correctness schema is `reason` then `verdict`,
and the user message contains the question, the reference, and the answer. Groundedness splits the
answer into claims and checks each one against the cited chunk text. An abstain makes no model call
and returns no claims. A wrapped reply is trimmed once and validated again, same as the answer call.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import litellm
from pydantic import BaseModel, Field, ValidationError

from src.rag.answer import ABSTAIN
from src.rag.config import ANSWER_RETRIES, ANSWER_TIMEOUT, JUDGE_MODEL, RAG_PROMPTS
from src.rag.llm_rag import _cost

JUDGE_VERSION = "judge-v1"
CORRECT_PROMPT = RAG_PROMPTS / JUDGE_VERSION / "correct.txt"
GROUNDED_PROMPT = RAG_PROMPTS / JUDGE_VERSION / "grounded.txt"


class Verdict(BaseModel):
    reason: str = Field(description="Why the answer is correct or incorrect, written before the verdict")
    verdict: str = Field(description='Either "correct" or "incorrect"')


class Claim(BaseModel):
    claim: str
    supported: bool


class Claims(BaseModel):
    reason: str = Field(description="How the answer was split into claims, written before the claims")
    claims: list[Claim]


@dataclass(frozen=True)
class Judgement:
    passed: bool | None
    reason: str
    unsupported: tuple[str, ...]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


Complete = Callable[[str, str, type[BaseModel]], tuple[BaseModel, int, int, float]]


def judge_correct(question: str, reference: str, answer: str, *,
                  complete: Complete | None = None, system_path: Path = CORRECT_PROMPT) -> Judgement:
    """Grade the answer against the reference. `passed` is true only for verdict `correct`."""
    user = f"Question: {question}\nReference: {reference}\nAnswer: {answer}"
    parsed, prompt, completion, cost = (complete or _complete)(system_path.read_text(encoding="utf-8"), user, Verdict)
    return Judgement(parsed.verdict.strip().lower() == "correct", parsed.reason, (), prompt, completion, cost)


def judge_grounded(answer: str, found: bool, sources: list[tuple[str, str]], *,
                   complete: Complete | None = None, system_path: Path = GROUNDED_PROMPT) -> Judgement:
    """Check the answer against cited texts. An abstain returns no claims and does not call the model."""
    if not found or answer.strip() == ABSTAIN:
        return Judgement(None, "", (), 0, 0, 0.0)
    blocks = "\n\n".join(f"[{header}]\n{text}" for header, text in sources) or "(no cited source text)"
    user = f"<sources>\n{blocks}\n</sources>\n\n<answer>\n{answer}\n</answer>"
    parsed, prompt, completion, cost = (complete or _complete)(system_path.read_text(encoding="utf-8"), user, Claims)
    unsupported = tuple(item.claim for item in parsed.claims if not item.supported)
    passed = bool(parsed.claims) and not unsupported
    return Judgement(passed, parsed.reason, unsupported, prompt, completion, cost)


def _complete(system: str, user: str, model: type[BaseModel], *, name: str = JUDGE_MODEL) -> tuple[BaseModel, int, int, float]:
    resp = litellm.completion(
        model=name, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format=model, temperature=0, timeout=ANSWER_TIMEOUT, num_retries=ANSWER_RETRIES,
    )
    parsed = _validate(model, resp.choices[0].message.content or "")
    usage = resp.usage
    return parsed, usage.prompt_tokens or 0, usage.completion_tokens or 0, _cost(resp)


def _validate(model: type[BaseModel], content: str) -> BaseModel:
    try:
        return model.model_validate_json(content)
    except ValidationError:
        return model.model_validate_json(_trim(content))


def _trim(content: str) -> str:
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text
