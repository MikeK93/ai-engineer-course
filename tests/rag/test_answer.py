"""Answer-path tests. A fake completion stands in for the model, and a word counter for tiktoken."""

import json
from types import SimpleNamespace

from src.rag.answer import ABSTAIN, answer_question
from src.rag.context import pack_context
from src.rag.llm_rag import RagAnswer, user_message


def words(text: str) -> int:
    return len(text.split())


def hit(i, text, n_words=None):
    body = text if n_words is None else " ".join(f"w{i}" for i in range(n_words))
    chunk = {"chunk_id": f"d#{i}", "source": f"pdfs/{i}.pdf", "section": f"Section {i}", "as_of": "2024-01",
             "text": body, "page_start": i + 1, "page_end": i + 1}
    return SimpleNamespace(chunk=chunk)


def completion(found, answer, citations, **extra):
    from src.rag.llm_rag import Completion

    return Completion(found, answer, citations, extra.get("prompt_tokens", 10), extra.get("completion_tokens", 5),
                      extra.get("cost_usd", 0.001), extra.get("latency_s", 0.2))


# --- packing ----------------------------------------------------------------------

def test_pack_keeps_rank_order_labels_and_skips_what_does_not_fit():
    hits = [hit(0, "alpha " * 30), hit(1, "beta " * 80), hit(2, "gamma " * 20)]
    packed = pack_context(hits, budget=80, count=words)
    assert list(packed.labels) == ["S1", "S2"]
    assert packed.labels["S1"]["chunk_id"] == "d#0" and packed.labels["S2"]["chunk_id"] == "d#2"
    assert packed.skipped == ["d#1"]
    assert "[S1] pdfs/0.pdf · Section 0 · 2024-01" in packed.text
    assert "beta" not in packed.text and packed.n_tokens <= 80


def test_pack_shows_the_embed_prefix_when_the_body_omits_the_city():
    item = hit(0, "Lease Rate/Mo: $7,937 and a fenced contractor's yard.")
    item.chunk["embed_prefix"] = "16213 Illinois Ave, Paramount, CA - Industrial For Lease | Illinois Ave/Monroe St"
    packed = pack_context([item], budget=1000, count=words)
    assert "Paramount" in packed.text and "$7,937" in packed.text


def test_pack_of_nothing_is_empty():
    assert pack_context([], budget=100, count=words).labels == {}


# --- citations and abstain --------------------------------------------------------

def test_no_hits_abstains_without_calling_the_model(tmp_path):
    calls = []
    result = answer_question("price?", hits=[], complete=lambda q, s: calls.append(1), log_path=tmp_path / "a.jsonl")
    assert calls == [] and result.found is False and result.answer == ABSTAIN and result.citations == []
    assert json.loads((tmp_path / "a.jsonl").read_text())["retrieved_ids"] == []


def test_citations_are_normalised_unknowns_dropped_and_duplicates_collapsed():
    hits = [hit(0, "Asking price $1,189,900."), hit(1, "Five units.")]
    result = answer_question(
        "price?", hits=hits, budget=1000, complete=lambda q, s: completion(True, "It is $1,189,900.", ["[S1]", "S1", "S9", "nope"]))
    assert result.found is True and result.answer == "It is $1,189,900."
    assert [c.label for c in result.citations] == ["S1"]
    assert result.cited_ids == ["d#0"] and result.invalid_labels == ["S9", "nope"]
    assert result.citations[0].source == "pdfs/0.pdf" and result.citations[0].section == "Section 0"


def test_found_with_no_valid_citation_becomes_abstain():
    result = answer_question("price?", hits=[hit(0, "something stated here")], budget=1000,
                             complete=lambda q, s: completion(True, "I think $5.", ["S4"]))
    assert result.found is False and result.answer == ABSTAIN and result.citations == []
    assert result.invalid_labels == ["S4"] and result.prompt_tokens == 10


def test_model_abstain_is_replaced_by_the_constant_sentence():
    result = answer_question("price?", hits=[hit(0, "unrelated text here")], budget=1000,
                             complete=lambda q, s: completion(False, "Cannot tell.", []))
    assert result.answer == ABSTAIN and result.cited_ids == []


def test_prompt_states_the_rules_and_the_abstain_sentence():
    from src.rag.llm_rag import SYSTEM_PROMPT

    text = SYSTEM_PROMPT.read_text(encoding="utf-8")
    assert ABSTAIN in text and "<sources>" in text
    for rule in ("exactly as written", "comparable", "later as_of", "fund", "listing", "similar"):
        assert rule in text
    assert user_message("Where?", "body").startswith("<sources>\nbody\n</sources>")


def test_complete_rag_sends_the_model_as_the_schema_and_validates_it():
    from src.rag.llm_rag import complete_rag, litellm

    seen = {}

    def fake_completion(**kwargs):
        seen["response_format"] = kwargs["response_format"]
        seen["temperature"] = kwargs["temperature"]
        body = RagAnswer(found=True, answer="Price is $1.", citations=["S1"]).model_dump_json()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=body))],
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=4, cost=0.01),
        )

    original = litellm.completion
    litellm.completion = fake_completion
    try:
        result = complete_rag("price?", "sources")
    finally:
        litellm.completion = original
    assert seen["response_format"] is RagAnswer and seen["temperature"] == 0
    assert result.found is True and result.answer == "Price is $1." and result.citations == ["S1"]
    assert result.cost_usd == 0.01


def test_parse_falls_back_to_trimming_a_wrapped_reply():
    import pytest
    from pydantic import ValidationError

    from src.rag.llm_rag import _parse

    raw = '{"found": true, "answer": "Price is $1.", "citations": ["S1"]}'
    wrapped = "Here is the answer:\n```json\n" + raw + "\n```"
    assert _parse(raw).citations == ["S1"]
    assert _parse(wrapped).answer == "Price is $1."
    with pytest.raises(ValidationError):
        _parse('```json\n{"found": true}\n```')


def test_schema_rejects_a_missing_field():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RagAnswer.model_validate_json('{"found": true, "answer": "x"}')
