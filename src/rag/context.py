"""Fit retrieved chunks into the answer prompt. Public API: `pack_context`.

Chunks are taken in rank order. A chunk that does not fit in `CONTEXT_BUDGET` is skipped and the next
one is tried, so one long chunk cannot push out a shorter one behind it. Packed chunks are labelled
`S1`, `S2`, ... and the header of each is `source · section · as_of`. The token counter is tiktoken,
because this budget limits the answer model's prompt, not the embedding model. It is injected, so
tests do not depend on an encoding.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache

from .config import ANSWER_ENCODING, CONTEXT_BUDGET


@dataclass
class PackedContext:
    text: str                          # the <sources> body
    labels: dict[str, dict] = field(default_factory=dict)   # "S1" -> chunk
    skipped: list[str] = field(default_factory=list)        # chunk ids that did not fit, in rank order
    n_tokens: int = 0


def pack_context(hits: list, *, budget: int = CONTEXT_BUDGET,
                 count: Callable[[str], int] | None = None) -> PackedContext:
    count = count or answer_tokens
    packed = PackedContext("")
    for hit in hits:
        chunk = hit.chunk
        label = f"S{len(packed.labels) + 1}"
        block = _block(label, chunk)
        extra = count("\n\n" + block) if packed.labels else count(block)
        if packed.n_tokens + extra > budget:
            packed.skipped.append(chunk["chunk_id"])
            continue
        packed.text = f"{packed.text}\n\n{block}" if packed.text else block
        packed.labels[label] = chunk
        packed.n_tokens += extra
    return packed


def _block(label: str, chunk: dict) -> str:
    header = f"[{label}] {chunk['source']} · {chunk['section']} · {chunk['as_of']}"
    return f"{header}\n{chunk['text']}"


@lru_cache(maxsize=1)
def _encoding():
    import tiktoken

    return tiktoken.get_encoding(ANSWER_ENCODING)


def answer_tokens(text: str) -> int:
    return len(_encoding().encode(text or ""))
