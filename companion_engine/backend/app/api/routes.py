"""API 路由文件，负责接收 HTTP 请求并调用对话引擎和存储模块。"""

from fastapi import APIRouter, HTTPException

from app.core.engine import handle_event
from app.db.connection import get_connection
from app.db.init_db import init_db
from app.memory.long_term_memory_store import (
    get_important_memories,
    get_recent_memories,
)
from app.memory.profile_store import get_profile
from app.llm.local_gguf_client import LocalModelError, get_last_error
from app.persona.persona_store import get_current_persona, save_persona
from app.relationship.relationship_store import get_relationship_state
from app.schemas.engine import EngineInput, EngineOutput
from app.schemas.persona import PersonaSnapshot

router = APIRouter() 

DEFAULT_DB_PATH = "../data/companion.db"
RESET_TABLES = [
    "user_profile",
    "persona_state",
    "persona_preferences",
    "relationship_state",
    "long_term_memories",
    "conversation_logs",
    "short_term_dialogue",
    "emotion_traces",
    "proactive_logs",
    "interaction_feedback",
]


@router.get("/health")
def health_check() -> dict[str, str]:
    """健康检查接口，用于确认服务已经正常启动。"""
    return {"status": "ok"}


@router.post("/api/chat")
def chat(input_data: EngineInput, use_local_model: bool = True) -> EngineOutput:
    """对话接口，接收引擎输入并返回引擎输出。"""
    _ = use_local_model
    try:
        return handle_event(
            input_data=input_data,
            db_path=DEFAULT_DB_PATH,
            use_local_model=True,
        )
    except LocalModelError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": str(exc),
                "local_model_error": get_last_error(),
                "mock_disabled": True,
            },
        ) from exc


@router.get("/api/state/{user_id}")
def get_state(user_id: str) -> dict[str, object]:
    """读取用户当前画像、Persona、关系状态和长期记忆。"""
    init_db(DEFAULT_DB_PATH)

    user_profile = get_profile(user_id=user_id, db_path=DEFAULT_DB_PATH)
    persona = get_current_persona(user_id=user_id, db_path=DEFAULT_DB_PATH)
    relationship_state = get_relationship_state(user_id=user_id, db_path=DEFAULT_DB_PATH)
    recent_memories = get_recent_memories(user_id=user_id, limit=5, db_path=DEFAULT_DB_PATH)
    important_memories = get_important_memories(user_id=user_id, limit=5, db_path=DEFAULT_DB_PATH)

    return {
        "user_profile": user_profile,
        "persona": persona,
        "relationship_state": relationship_state,
        "recent_memories": recent_memories,
        "important_memories": important_memories,
    }


@router.post("/api/persona/{user_id}")
def update_persona(user_id: str, persona: PersonaSnapshot) -> dict[str, str]:
    """保存指定用户的稳定 Persona。"""
    init_db(DEFAULT_DB_PATH)
    save_persona(user_id=user_id, persona=persona, db_path=DEFAULT_DB_PATH)
    return {"status": "ok"}


@router.post("/api/reset/{user_id}")
def reset_user(user_id: str) -> dict[str, str]:
    """删除指定用户的测试数据，便于前端和开发阶段重新开始。"""
    init_db(DEFAULT_DB_PATH)
    conn = get_connection(DEFAULT_DB_PATH)

    try:
        # 只删除该用户相关数据，不影响其他用户的测试记录。
        for table_name in RESET_TABLES:
            conn.execute(f"DELETE FROM {table_name} WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    return {"status": "ok"}
