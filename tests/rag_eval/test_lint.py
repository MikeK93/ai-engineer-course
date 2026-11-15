"""Test-set lint. Chunks are invented; nothing is read from data/."""

from src.rag.answer import ABSTAIN
from src.rag_eval.lint import lint


def chunk(doc, i, text):
    return {"chunk_id": f"{doc}#{i}", "doc_id": doc, "text": text}


def case(case_id, kind="exact", **over):
    row = {
        "id": case_id, "kind": kind, "question": "What is the price?", "source": "a",
        "evidence": ["price $1"], "must": [["$1"]], "reference": "$1",
    }
    row.update(over)
    return row


def no_answer(case_id, source="a"):
    return {"id": case_id, "kind": "no-answer", "question": "What is the price?",
            "source": source, "reference": ABSTAIN}


CHUNKS = [chunk("a", 0, "The price $1 is firm."), chunk("a", 1, "It has 33 units."), chunk("b", 0, "Another building.")]


def test_a_heading_kept_only_in_the_embed_prefix_still_counts():
    chunks = [chunk("a", 0, "The Pavilion, Cricket Square"), chunk("a", 1, "The price $1 is firm.")]
    chunks[0]["embed_prefix"] = "OAM | Principal Office of the Fund:"
    rows = [
        case("e01", evidence=["Principal Office of the Fund:"], must=[["Principal Office of the Fund:"]]),
        case("e02"),
    ]
    result = lint(rows, chunks)
    assert result.ok
    assert result.chunk_ids["e01"] == ("a#0",)


def test_a_quote_in_one_document_resolves_to_that_chunk():
    result = lint([case("e01"), case("e02", evidence=["33 units"], must=[["33 units"]])], CHUNKS)
    assert result.ok
    assert result.chunk_ids == {"e01": ("a#0",), "e02": ("a#1",)}


def test_a_quote_that_is_also_in_another_document_fails():
    chunks = CHUNKS + [chunk("b", 1, "The price $1 is repeated.")]
    result = lint([case("e01"), case("e02", evidence=["33 units"], must=[["33 units"]])], chunks)
    assert not result.ok and any("also in b" in error for error in result.errors)
    assert "e01" not in result.chunk_ids and result.chunk_ids["e02"] == ("a#1",)


def test_must_is_or_inside_a_group_and_has_to_be_in_the_evidence_chunk():
    rows = [
        case("e01", must=[["missing", "$1"]]),
        case("e02", evidence=["33 units"], must=[["$1"]]),
    ]
    result = lint(rows, CHUNKS)
    assert result.chunk_ids["e01"] == ("a#0",)
    assert any("e02" in error and "$1" in error and "a#1" in error for error in result.errors)


def test_two_sources_each_keep_their_own_quote():
    rows = [
        case("o01", kind="outdated-version", source=["add", "orig"],
             evidence=["principal office", "registered office"], must=[["principal office"], ["registered office"]]),
        case("o02", kind="outdated-version", source=["add", "orig"],
             evidence=["principal office"], must=[["principal office"]]),
    ]
    chunks = [chunk("add", 0, "send it to the principal office"), chunk("orig", 0, "send it to the registered office")]
    result = lint(rows, chunks)
    assert result.chunk_ids["o01"] == ("add#0", "orig#0")
    assert any("orig contains none of the evidence" in error for error in result.errors)


def test_a_quote_in_both_listed_documents_is_not_exact():
    rows = [
        case("o01", source=["add", "orig"], evidence=["the office"], must=[["office"]]),
        case("o02", source="orig", evidence=["only here"], must=[["only here"]]),
    ]
    chunks = [chunk("add", 0, "the office"), chunk("orig", 0, "the office and only here")]
    result = lint(rows, chunks)
    assert any("o01" in error and "not exactly one" in error for error in result.errors)
    assert result.chunk_ids["o02"] == ("orig#0",)


def test_multi_chunk_evidence_must_land_in_two_chunks():
    rows = [
        case("m01", kind="multi-chunk", evidence=["price $1", "33 units"], must=[["$1"], ["33 units"]]),
        case("m02", kind="multi-chunk", evidence=["price $1", "$1 is firm"], must=[["$1"], ["firm"]]),
    ]
    result = lint(rows, CHUNKS)
    assert result.chunk_ids["m01"] == ("a#0", "a#1")
    assert any("m02" in error and "a#0" in error for error in result.errors)


def test_no_answer_rejects_evidence_and_a_wrong_reference():
    rows = [
        no_answer("n01"),
        no_answer("n02", source=None),
        {**no_answer("n03"), "evidence": ["price $1"]},
        {**no_answer("n04"), "reference": "unknown"},
    ]
    result = lint(rows, CHUNKS)
    assert result.chunk_ids["n01"] == () and result.chunk_ids["n02"] == ()
    assert any("n03" in error and "no evidence" in error for error in result.errors)
    assert any("n04" in error and ABSTAIN in error for error in result.errors)


def test_duplicate_ids_unknown_sources_and_a_single_case_of_a_kind_fail():
    rows = [case("e01"), case("e01"), case("e02", source="missing"), case("p01", kind="paraphrase")]
    result = lint(rows, CHUNKS)
    text = "\n".join(result.errors)
    assert "duplicate id" in text
    assert "missing" in text and "not a document" in text
    assert "kind 'paraphrase' has 1 case" in text
