"""One answer call. Public API: `complete_rag`, `RagAnswer`.

A new LiteLLM call, separate from `src/llm.py` (that one extracts listings and is not used here).
`response_format` is the `RagAnswer` model. The body is validated with that model; if the
provider wrapped the JSON, fences and surrounding text are trimmed and validation is tried once more.
Temperature is 0.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path

import litellm
from pydantic import BaseModel, Field, ValidationError

from .config import ANSWER_RETRIES, ANSWER_TIMEOUT, RAG_MODEL, RAG_PROMPTS

litellm.suppress_debug_info = True

PROMPT_VERSION = "v2"
SYSTEM_PROMPT = RAG_PROMPTS / PROMPT_VERSION / "system.txt"


class RagAnswer(BaseModel):
    found: bool = Field(description="True only when the sources state the answer to the question")
    answer: str = Field(description="The answer in words, or the abstain sentence when found is false")
    citations: list[str] = Field(description="Labels of the sources used, such as S1")


@dataclass(frozen=True)
class Completion:
    found: bool
    answer: str
    citations: list[str]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_s: float


def user_message(question: str, sources: str) -> str:
    return f"<sources>\n{sources}\n</sources>\n\nQuestion: {question}"


def complete_rag(question: str, sources: str, *, model: str = RAG_MODEL,
                 system_path: Path = SYSTEM_PROMPT) -> Completion:
    """Ask the model. `sources` is the packed context from `pack_context`."""
    messages = [
        {"role": "system", "content": system_path.read_text(encoding="utf-8")},
        {"role": "user", "content": user_message(question, sources)},
    ]
    started = time.perf_counter()
    resp = litellm.completion(
        model=model, messages=messages, response_format=RagAnswer,
        temperature=0, timeout=ANSWER_TIMEOUT, num_retries=ANSWER_RETRIES,
    )
    parsed = _parse(resp.choices[0].message.content or "")
    usage = resp.usage
    return Completion(
        found=parsed.found, answer=parsed.answer, citations=list(parsed.citations),
        prompt_tokens=usage.prompt_tokens or 0, completion_tokens=usage.completion_tokens or 0,
        cost_usd=_cost(resp), latency_s=time.perf_counter() - started,
    )


def _parse(content: str) -> RagAnswer:
    """Validate the body. A wrapped reply is trimmed once and validated again."""
    try:
        return RagAnswer.model_validate_json(content)
    except ValidationError:
        return RagAnswer.model_validate_json(_trim(content))


def _trim(content: str) -> str:
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text


def _cost(resp) -> float:
    """OpenRouter returns usage.cost; direct providers use LiteLLM's price table. Unknown price -> 0."""
    usage = resp.usage
    if usage is not None and isinstance(getattr(usage, "cost", None), (int, float)):
        return float(usage.cost)
    hidden = getattr(resp, "_hidden_params", None) or {}
    if isinstance(hidden.get("response_cost"), (int, float)):
        return float(hidden["response_cost"])
    try:
        return float(litellm.completion_cost(completion_response=resp))
    except Exception:
        return 0.0
