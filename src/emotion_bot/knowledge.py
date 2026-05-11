"""Knowledge folder ingestion for RAG documents."""

from __future__ import annotations

from pathlib import Path

from .storage import MemoryStore
from .text_index import chunk_text, embedding_backend_name


def read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def ingest_knowledge_dir(store: MemoryStore, knowledge_dir: Path) -> dict:
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(knowledge_dir.glob("*.txt"))
    ingested: list[dict] = []
    skipped: list[str] = []
    rebuilt: list[str] = []
    current_backend = embedding_backend_name()

    for path in files:
        source = str(path.resolve())
        existing_backend = store.document_source_backend(source)
        if existing_backend == current_backend:
            skipped.append(path.name)
            continue
        if existing_backend is not None:
            store.delete_documents_by_source(source)
            rebuilt.append(path.name)

        text = read_text_file(path)
        chunks = chunk_text(text)
        for chunk in chunks:
            store.add_document(
                title=path.stem,
                content=chunk,
                source=source,
                user_id=None,
                weight=1.0,
            )
        ingested.append({"file": path.name, "chunks": len(chunks)})

    return {
        "files": len(files),
        "ingested": ingested,
        "rebuilt": rebuilt,
        "skipped": skipped,
        "embedding_backend": current_backend,
        "document_chunks": store.count_documents(),
    }
