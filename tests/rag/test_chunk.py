"""Chunking tests. A word counter stands in for the embedding tokenizer, so nothing is downloaded."""

import json
import re

from src.rag.chunk import chunk_corpus, chunk_document
from measurements.chunking.fixed import fixed_chunks
from src.rag.config import ChunkPaths
from src.rag.store import write_markdown
from src.rag.models import Page


def words(text: str) -> int:
    return len(text.split())


def front(**extra):
    base = {"doc_id": "pdfs__x", "title": "Test Doc", "source": "pdfs/x.pdf", "doc_type": "listing",
            "as_of": "2024", "content_hash": "abc", "pages": "1-3"}
    return {**base, **extra}


def sentence(n: int, tag: str) -> str:
    return " ".join(f"{tag}{i}" for i in range(n)) + "."


def test_small_parent_keeps_its_child_subsection():
    body = f"# Parent\n\nshort intro\n\n## Child\n\n{sentence(50, 'c')}\n"
    [chunk] = chunk_document(front(), body, words, target=200, cap=300, min_tokens=40)
    assert chunk.section == "Parent" and "Child\n\nc0 " in chunk.text


def test_boilerplate_section_does_not_swallow_the_following_section():
    body = (f"# Table of Contents\n\nSummary . . . 4\n\n## Offering Summary\n\n| Price | $1,250,000 |\n|---|---|\n"
            f"| Size | 34,076 SF |\n\n{sentence(30, 'o')}\n")
    chunks = chunk_document(front(), body, words, target=200, cap=300, min_tokens=40)
    assert [(c.section, c.kind) for c in chunks] == [("Table of Contents", "boilerplate"), ("Offering Summary", "content")]
    assert "$1,250,000" in chunks[1].text


def test_title_like_line_stays_with_the_paragraph_after_it():
    body = f"# H\n\n{sentence(30, 'a')}\n\nINVESTMENT OVERVIEW\n\n{sentence(30, 'b')}\n"
    chunks = chunk_document(front(), body, words, target=40, cap=100, min_tokens=10)
    assert len(chunks) == 2
    assert chunks[1].text.startswith("INVESTMENT OVERVIEW") and "INVESTMENT" not in chunks[0].text


def test_sections_follow_headings_and_sibling_sections_stay_separate():
    body = f"""<!-- page 1 -->

# Offering

## Pricing

{sentence(120, 'p')}

## Terms

short note here

## Location

{sentence(120, 'l')}
"""
    chunks = chunk_document(front(), body, words, target=200, cap=300, min_tokens=40)
    # Sibling sections never merge, even when one is tiny: the label always says where the text came from.
    assert [c.section for c in chunks] == ["Offering > Pricing", "Offering > Terms", "Offering > Location"]
    assert chunks[1].text == "short note here"
    assert all(c.section_source == "heading" for c in chunks)
    assert chunks[0].embed_prefix == "Test Doc | Offering > Pricing"


def test_no_heading_falls_back_to_page_section_and_title_prefix():
    body = f"<!-- page 2 -->\n\n{sentence(50, 'a')}\n"
    [chunk] = chunk_document(front(pages="2-2"), body, words)
    assert (chunk.section, chunk.section_source, chunk.embed_prefix) == ("Test Doc > page 2", "page", "Test Doc")
    assert (chunk.page_start, chunk.page_end) == (2, 2)


def test_table_splits_between_rows_and_repeats_header():
    rows = "\n".join(f"| item {i} | value {i} | note {i} |" for i in range(40))
    body = f"# Rent roll\n\n| Unit | Rent | Note |\n|---|---|---|\n{rows}\n"
    chunks = chunk_document(front(), body, words, target=60, cap=90)
    assert len(chunks) > 1
    for chunk in chunks:
        lines = chunk.text.split("\n")
        assert lines[0] == "| Unit | Rent | Note |" and lines[1] == "|---|---|---|"
        assert all(line.startswith("|") and line.endswith("|") for line in lines)
        assert chunk.n_tokens <= 90
    all_rows = [line for c in chunks for line in c.text.split("\n")[2:]]
    assert all_rows == rows.split("\n")                      # every row exactly once, in order


def test_one_row_table_with_a_huge_cell_becomes_several_complete_rows():
    long_cell = " ".join(sentence(20, f"S{i}_") for i in range(10))          # 200 words in one cell
    body = f"# Terms\n\n| Item | Detail |\n|---|---|\n| Minimum Subscription | {long_cell} |\n"
    chunks = chunk_document(front(), body, words, target=80, cap=100)
    assert len(chunks) >= 3 and all(c.n_tokens <= 100 for c in chunks)
    for chunk in chunks:
        lines = chunk.text.split("\n")
        assert lines[0] == "| Item | Detail |"
        assert all(line.startswith("|") and line.endswith("|") for line in lines)
        assert all(line.startswith("|Minimum Subscription|") for line in lines[2:])      # label repeated, row whole


def test_oversized_paragraph_is_cut_at_sentences_and_respects_the_cap():
    paragraph = " ".join(sentence(30, f"S{i}_") for i in range(10))     # 300 words, 10 sentences
    chunks = chunk_document(front(), f"# Big\n\n{paragraph}\n", words, target=100, cap=120)
    assert len(chunks) >= 3
    assert all(c.n_tokens <= 120 for c in chunks)
    assert all(c.text.rstrip().endswith(".") for c in chunks)       # cut between sentences, not inside one


def test_boilerplate_by_heading_and_by_legal_phrase():
    body = (f"# Confidentiality and Disclaimer\n\n{sentence(40, 'x')}\n\n# Details\n\n"
            "This information supplied herein is from sources we deem reliable. It is provided without warranty.\n\n"
            f"# Facts\n\n{sentence(200, 'f')}\n")
    chunks = chunk_document(front(), body, words, target=60, cap=100, min_tokens=10)
    kinds = {c.section: c.kind for c in chunks}
    assert kinds["Confidentiality and Disclaimer"] == "boilerplate"
    assert kinds["Details"] == "boilerplate"
    assert kinds["Facts"] == "content"


def test_ocr_flag_follows_the_pages_in_the_chunk():
    body = f"<!-- page 1 -->\n\n# A\n\n{sentence(150, 'a')}\n\n<!-- page 2 -->\n\n# B\n\n{sentence(150, 'b')}\n"
    chunks = chunk_document(front(ocr_pages=[2]), body, words, target=200, cap=300, min_tokens=20)
    assert [(c.section, c.ocr, c.page_start) for c in chunks] == [("A", False, 1), ("B", True, 2)]


def test_version_fields_and_stable_ids():
    body = f"# Fees\n\n{sentence(30, 'z')}\n"
    first = chunk_document(front(doc_id="pdfs__om@addendum-1", version_of="pdfs__om", replaces="fees", as_of="2021-12-23"), body, words)
    second = chunk_document(front(doc_id="pdfs__om@addendum-1", version_of="pdfs__om", replaces="fees", as_of="2021-12-23"), body, words)
    assert first == second and first[0].chunk_id == "pdfs__om@addendum-1#0"
    assert (first[0].version_of, first[0].replaces, first[0].as_of) == ("pdfs__om", "fees", "2021-12-23")


def test_chunk_corpus_writes_jsonl_and_summary(tmp_path):
    md = tmp_path / "md"
    write_markdown(md / "pdfs__x.md", front(), [Page(number=1, text=f"# Heading\n\n{sentence(60, 'w')}")])
    paths = ChunkPaths(md=md, manifest=tmp_path / "none.json", chunks=tmp_path / "chunks.jsonl",
                       summary=tmp_path / "summary.json")
    summary = chunk_corpus(paths=paths, count=words, log=lambda _: None)
    rows = [json.loads(line) for line in paths.chunks.read_text(encoding="utf-8").splitlines()]
    assert summary["n_chunks"] == len(rows) == 1 and summary["over_cap"] == []
    assert rows[0]["section"] == "Heading" and rows[0]["chunk_id"] == "pdfs__x#0"
    assert json.loads(paths.summary.read_text())["docs"]["pdfs__x"]["chunks"] == 1


def test_compare_targets_come_from_config(tmp_path):
    from measurements.chunking.compare import load_targets

    path = tmp_path / "chunk_compare.yaml"
    path.write_text("documents:\n  - match: gs01_\n  - {match: Centurion, pages: 40}\n", encoding="utf-8")
    assert load_targets(path) == (("gs01_", None), ("Centurion", 40))


def test_fixed_windows_cut_through_table_rows_and_overlap():
    body = "\n".join(f"| a{i} | b{i} |" for i in range(30))
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", body)]     # one token per word
    chunks = fixed_chunks(front(), body, size=22, overlap=5, spans_of=lambda _: spans)
    assert len(chunks) > 1 and all(c.section == "" for c in chunks)
    cut = sum(1 for c in chunks for line in c.text.split("\n") if line.startswith("|") != line.endswith("|"))
    assert cut > 0                                                        # the baseline's weakness
    assert chunks[1].text.split()[0] in chunks[0].text.split()           # windows overlap
