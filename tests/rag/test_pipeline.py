"""rag-all skips chunk and index when the inputs are unchanged. No models and no files."""

from src.rag.pipeline import chunk_current, index_current, index_stamp, run_all


def test_chunk_is_current_only_when_the_dataset_and_pipeline_match():
    summary = {"dataset_version": "abc", "pipeline_version": "rag-v3"}
    assert chunk_current(summary, dataset_version="abc", pipeline_version="rag-v3")
    assert not chunk_current(None, dataset_version="abc", pipeline_version="rag-v3")
    assert not chunk_current(summary, dataset_version="newer", pipeline_version="rag-v3")
    assert not chunk_current(summary, dataset_version="abc", pipeline_version="rag-v4")


def test_index_stamp_includes_the_model():
    assert index_current(index_stamp("abc", "bge"), "abc", "bge")
    assert not index_current(index_stamp("abc", "bge"), "abc", "other")
    assert not index_current(None, "abc", "bge")


def test_unchanged_inputs_skip_chunk_and_index():
    calls = []
    code = run_all(
        ingest=lambda: calls.append("ingest"),
        chunk=lambda: calls.append("chunk"),
        index=lambda: calls.append("index"),
        retrieval=lambda: calls.append("retrieval") or 0,
        answer=lambda: calls.append("answer") or 0,
        chunk_current=lambda: True,
        index_current=lambda: True,
        log=lambda _message: None,
    )
    assert code == 0
    assert calls == ["ingest", "retrieval", "answer"]


def test_changed_inputs_are_rebuilt_and_a_retrieval_failure_stops_the_run():
    calls = []
    code = run_all(
        ingest=lambda: calls.append("ingest"),
        chunk=lambda: calls.append("chunk"),
        index=lambda: calls.append("index"),
        retrieval=lambda: calls.append("retrieval") or 1,
        answer=lambda: calls.append("answer") or 0,
        chunk_current=lambda: False,
        index_current=lambda: False,
        log=lambda _message: None,
    )
    assert code == 1
    assert calls == ["ingest", "chunk", "index", "retrieval"]
