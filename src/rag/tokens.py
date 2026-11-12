"""Token counting with the embedding model's own tokenizer.

The embedding model (bge-small) reads at most 512 tokens and silently drops the rest, so chunk
sizes must be measured with its tokenizer, not an OpenAI one. This is the only module that
knows which tokenizer is used; everything else takes a `count(text) -> int` function.
"""

from functools import lru_cache

from .config import EMBED_MODEL


@lru_cache(maxsize=1)
def _tokenizer():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
    tok.model_max_length = 10**9          # we enforce the 512 limit ourselves; silence the length warning
    return tok


def count_tokens(text: str) -> int:
    """Tokens the embedding model would see for `text` (without the two special tokens)."""
    if not text:
        return 0
    return len(_tokenizer()(text, add_special_tokens=False)["input_ids"])


def token_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) character offsets of every token in `text`, for cutting text by token count."""
    if not text:
        return []
    encoded = _tokenizer()(text, add_special_tokens=False, return_offsets_mapping=True)
    return [tuple(span) for span in encoded["offset_mapping"]]
