"""FastAPI entrypoint for Emotion Bot."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .chat import ChatRequest, ChatResponse, ChatService, DocumentIngestRequest
from .config import get_settings
from .llm import LLMError, build_llm
from .memory import MemoryManager
from .proactive import ProactiveEngine
from .storage import MemoryStore
from .text_index import chunk_text


settings = get_settings()
store = MemoryStore(settings.db_path)
memory_manager = MemoryManager(store)
llm = build_llm(settings)
proactive_engine = ProactiveEngine(store)
chat_service = ChatService(settings, store, memory_manager, llm, proactive_engine)

app = FastAPI(title="Emotion Bot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "model_path": str(settings.model_path),
        "model_exists": settings.model_path.exists(),
        "db_path": str(settings.db_path),
        "llm_backend": settings.llm_backend,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return chat_service.chat(request)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/users")
def users() -> dict:
    return {"users": store.list_users()}


@app.get("/api/users/{user_id}/memory")
def user_memory(user_id: str, limit: int = Query(default=50, ge=1, le=200)) -> dict:
    store.ensure_user(user_id)
    return {
        "user_id": user_id,
        "profile_summary": store.get_profile_summary(user_id),
        "memories": store.list_memories(user_id, limit=limit),
        "recent_messages": store.recent_messages(user_id, limit=20),
    }


@app.post("/api/documents")
def ingest_document(request: DocumentIngestRequest) -> dict:
    chunks = chunk_text(request.content)
    ids = [
        store.add_document(
            title=request.title,
            content=chunk,
            source=request.source,
            user_id=request.user_id,
            weight=request.weight,
        )
        for chunk in chunks
    ]
    return {"ok": True, "document_ids": ids, "chunks": len(ids)}


@app.get("/api/proactive/check")
def proactive_check(
    user_id: str = Query(default="default", min_length=1),
    scenario: str | None = Query(default=None, max_length=120),
    persist: bool = Query(default=True),
) -> dict:
    suggestion = proactive_engine.check(user_id=user_id, scenario=scenario, persist=persist)
    return suggestion.__dict__


def main() -> None:
    import uvicorn

    uvicorn.run(
        "emotion_bot.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
