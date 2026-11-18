"""One-command RAG run. Public API: `run_all`, `chunk_current`, `index_current`, `index_stamp`.

`ocr` is never called. Ingest still runs, and its extraction cache skips a file whose bytes did not
change. Chunk and index are skipped when their inputs match the last run.
"""

from collections.abc import Callable


def chunk_current(summary: dict | None, *, dataset_version: str | None, pipeline_version: str) -> bool:
    """True when `chunks.jsonl` was built from this dataset and this pipeline version."""
    return bool(
        summary
        and summary.get("dataset_version") == dataset_version
        and summary.get("pipeline_version") == pipeline_version
    )


def index_stamp(chunks_hash: str, model: str) -> str:
    """The stamp written after a successful index build."""
    return f"{model}\n{chunks_hash}\n"


def index_current(saved: str | None, chunks_hash: str, model: str) -> bool:
    """True when the index stamp matches the current chunks file and embedding model."""
    return saved == index_stamp(chunks_hash, model)


def run_all(*, ingest: Callable[[], None], chunk: Callable[[], None], index: Callable[[], None],
            retrieval: Callable[[], int], answer: Callable[[], int],
            chunk_current: Callable[[], bool], index_current: Callable[[], bool],
            log: Callable[[str], None] = print) -> int:
    """Ingest, chunk, index, retrieval eval, answer eval. Returns the answer-eval exit code."""
    log("rag-all: ingest")
    ingest()
    if chunk_current():
        log("rag-all: chunk skipped, inputs unchanged")
    else:
        log("rag-all: chunk")
        chunk()
    if index_current():
        log("rag-all: index skipped, inputs unchanged")
    else:
        log("rag-all: index")
        index()
    log("rag-all: retrieval")
    if retrieval() != 0:
        return 1
    log("rag-all: answer eval")
    return answer()
