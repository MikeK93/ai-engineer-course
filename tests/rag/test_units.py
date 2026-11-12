"""Unit tests for the small ingest modules. No models, no real PDFs."""

import pytest

from src.rag.dedup import find_duplicates
from src.rag.extract import extract_html
from src.rag.meta import CatalogError, DocEntry, VersionSpec, load_catalog
from src.rag.models import BLANK, OCR_REQUIRED, LogicalDoc, Page
from src.rag.normalize import normalize_pages
from src.rag.versions import find_version_markers, split_versions


def pages(*texts):
    return [Page(number=i, text=t, n_chars=len(t)) for i, t in enumerate(texts, 1)]


def doc(doc_id, text, version_of=None):
    return LogicalDoc(doc_id=doc_id, source="pdfs/x.pdf", title="t", doc_type="other", as_of="2020",
                      pages=pages(text), version_of=version_of)


# --- catalog ------------------------------------------------------------------

def write_catalog(tmp_path, yaml_text, files=("pdfs/a.pdf",)):
    for f in files:
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f).write_bytes(b"x")
    meta = tmp_path / "doc_meta.yaml"
    meta.write_text(yaml_text, encoding="utf-8")
    return meta


def test_catalog_loads_valid_entries(tmp_path):
    meta = write_catalog(tmp_path, "- {file: pdfs/a.pdf, title: A, doc_type: listing, as_of: 2021-05}\n")
    [entry] = load_catalog(meta, tmp_path)
    assert (entry.kind, entry.doc_id, entry.as_of) == ("pdf", "pdfs__a", "2021-05")


def test_catalog_reports_every_problem_at_once(tmp_path):
    meta = write_catalog(
        tmp_path,
        "- {file: pdfs/a.pdf, title: A, doc_type: nope, as_of: 21-05}\n- {file: pdfs/missing.pdf, title: B, doc_type: other, as_of: 2020}\n",
        files=("pdfs/a.pdf", "pdfs/orphan.pdf"),
    )
    with pytest.raises(CatalogError) as err:
        load_catalog(meta, tmp_path)
    message = str(err.value)
    assert "doc_type 'nope'" in message and "as_of" in message
    assert "no such file" in message and "orphan.pdf" in message


def test_catalog_requires_source_url_for_html(tmp_path):
    meta = write_catalog(tmp_path, "- {file: html/a.html, title: A, doc_type: listing, as_of: 2024}\n", files=("html/a.html",))
    with pytest.raises(CatalogError, match="source_url"):
        load_catalog(meta, tmp_path)


# --- html ---------------------------------------------------------------------

HTML = """<html><body><nav>Menu Login</nav><main>
<h1>5301 E 39th Ave</h1><p>Industrial building for sale.</p>
<table><tr><th>Type</th><td>Industrial</td></tr><tr><th>Size</th><td>10,000 | SF</td></tr></table>
<ul><li>Dock doors</li><li>Fenced yard</li></ul>
<script>var x = 1;</script><form>Contact us</form></main><footer>Copyright</footer></body></html>"""


def test_html_keeps_content_and_drops_chrome(tmp_path):
    path = tmp_path / "p.html"
    path.write_text(HTML, encoding="utf-8")
    [page] = extract_html(path)
    assert page.text.startswith("# 5301 E 39th Ave")
    assert "| Type | Industrial |" in page.text and "10,000 \\| SF" in page.text
    assert "- Dock doors\n- Fenced yard" in page.text
    for noise in ("Menu", "Contact us", "Copyright", "var x"):
        assert noise not in page.text


def test_html_unwraps_view_source_saves(tmp_path):
    lines = "".join(f'<tr><td class="line-content">{l}</td></tr>' for l in
                    ["&lt;html&gt;&lt;body&gt;&lt;main&gt;&lt;p&gt;Hello there&lt;/p&gt;&lt;/main&gt;&lt;/body&gt;&lt;/html&gt;"])
    path = tmp_path / "v.html"
    path.write_text(f"<html><body><table>{lines}</table></body></html>", encoding="utf-8")
    assert extract_html(path)[0].text == "Hello there"


# --- pdf page classification --------------------------------------------------

def test_pdf_pages_without_text_are_classified_by_drawings_and_images(tmp_path):
    import pymupdf
    from src.rag.extract import extract_pdf

    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "A readable page with enough characters to pass the text threshold easily.")
    outlined = doc.new_page()                       # no text layer: shapes only, like text turned into outlines
    for i in range(60):
        outlined.draw_rect(pymupdf.Rect(50 + i, 50, 52 + i, 90))
    doc.new_page()                                  # truly empty
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 20), False)
    doc.new_page().insert_image(pymupdf.Rect(50, 50, 150, 150), pixmap=pix)   # picture only
    path = tmp_path / "t.pdf"
    doc.save(path)

    statuses = [p.status for p in extract_pdf(path)]
    assert statuses == ["ok", OCR_REQUIRED, BLANK, OCR_REQUIRED]


# --- normalize ----------------------------------------------------------------

def test_normalize_cleans_text_markers_and_hyphenation():
    [page] = normalize_pages(pages("Fi\u200bne  spacing<br>here ﬁnal\n\n\n\nthe develop-\nment <!-- note -->plan"))
    assert page.text == "Fine spacing here final\n\nthe development plan"


def test_normalize_removes_repeating_headers_and_page_numbers_but_not_table_rows():
    body = [f"CONFIDENTIAL MEMO\n\nUnique content {'abcdefgh'[n - 1] * 5}\n\n| Unit | Beds |\n\n| {n}" for n in range(1, 9)]
    out = normalize_pages(pages(*body))
    for page in out:
        assert "CONFIDENTIAL" not in page.text
        assert page.text.endswith("| Beds |")          # page number gone, column header kept
        assert "Unique content" in page.text


def test_normalize_leaves_unreadable_pages_alone():
    blank = Page(number=1, text="", status=OCR_REQUIRED)
    assert normalize_pages([blank]) == [blank]


# --- versions -----------------------------------------------------------------

def entry(*versions):
    return DocEntry(file="pdfs/om.pdf", title="OM", doc_type="fund_om", as_of=None if versions else "2020",
                    versions=tuple(versions))


def test_split_versions_by_page_and_heading():
    ps = pages("intro", "body", "ADDENDUM No. 1\n\nnew terms", "more")
    docs = split_versions(entry(VersionSpec("original", 1, "2020"), VersionSpec("addendum-1", "Addendum", "2021", "terms")), ps)
    assert [d.doc_id for d in docs] == ["pdfs__om@original", "pdfs__om@addendum-1"]
    assert [d.page_range for d in docs] == ["1-2", "3-4"]
    assert docs[1].as_of == "2021" and docs[1].version_of == "pdfs__om"


def test_split_versions_rejects_bad_starts():
    with pytest.raises(ValueError, match="begin at page 1"):
        split_versions(entry(VersionSpec("a", 2, "2020")), pages("a", "b"))
    with pytest.raises(ValueError, match="not found"):
        split_versions(entry(VersionSpec("a", 1, "2020"), VersionSpec("b", "Nowhere", "2021")), pages("a", "b"))


def test_find_version_markers_suggests_addendum_pages():
    assert find_version_markers(pages("intro", "## Addendum No. 1", "text mentioning an addendum in prose")) == [(2, "## Addendum No. 1")]


# --- dedup --------------------------------------------------------------------

LONG = " ".join(f"word{i}" for i in range(200))


def test_dedup_exact_and_near_duplicates_keep_first_by_id():
    docs = [doc("b", LONG), doc("a", LONG), doc("c", LONG + " extra tail words"), doc("d", "completely different text " * 30)]
    dropped = find_duplicates(docs)
    assert set(dropped) == {"b", "c"}
    assert dropped["b"].kind == "exact_duplicate" and dropped["b"].of == "a"
    assert dropped["c"].kind == "near_duplicate"


def test_dedup_never_merges_versions_of_one_file():
    docs = [doc("om@original", LONG, version_of="om"), doc("om@addendum", LONG, version_of="om")]
    assert find_duplicates(docs) == {}
