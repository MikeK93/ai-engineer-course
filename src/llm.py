import time
from dataclasses import dataclass

import litellm

from .config import RunConfig
from .documents import Document
from .schema import RealEstateListing

litellm.suppress_debug_info = True


@dataclass
class LLMResult:
    content: str
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


def build_messages(system_prompt: str, doc: Document) -> list[dict]:
    if doc.pdf_b64:
        user = [
            {"type": "text", "text": "Extract the listing data from the attached PDF."},
            {
                "type": "file",
                "file": {
                    "filename": doc.source_file,
                    "file_data": f"data:application/pdf;base64,{doc.pdf_b64}",
                },
            },
        ]
    else:
        user = f"Document:\n\n{doc.text}"
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user}]


def _completion_cost_usd(resp) -> float:
    """OpenRouter returns usage.cost; direct providers use LiteLLM's price table."""
    usage = resp.usage
    if usage is not None:
        cost = getattr(usage, "cost", None)
        if isinstance(cost, (int, float)):
            return float(cost)
    hidden = getattr(resp, "_hidden_params", None) or {}
    response_cost = hidden.get("response_cost")
    if isinstance(response_cost, (int, float)):
        return float(response_cost)
    try:
        return float(litellm.completion_cost(completion_response=resp))
    except Exception:
        return 0.0


def complete(cfg: RunConfig, messages: list[dict]) -> LLMResult:
    """Single structured-output call; retries and timeout are handled by LiteLLM."""
    start = time.perf_counter()
    resp = litellm.completion(
        model=cfg.model,
        messages=messages,
        response_format=RealEstateListing,
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        timeout=cfg.timeout,
        num_retries=cfg.max_retries,
        **cfg.extra_params,
    )
    latency = time.perf_counter() - start
    cost = _completion_cost_usd(resp)
    usage = resp.usage
    return LLMResult(
        content=resp.choices[0].message.content or "",
        latency_s=latency,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cost_usd=cost,
    )
