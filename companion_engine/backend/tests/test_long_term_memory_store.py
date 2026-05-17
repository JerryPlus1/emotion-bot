"""长期记忆存储测试，验证保存、读取、标记和关键词搜索。"""

from pathlib import Path

from app.db.connection import get_connection
from app.db.init_db import init_db
from app.memory.long_term_memory_store import (
    add_long_term_memory,
    get_important_memories,
    get_recent_memories,
    mark_memory_used,
    search_memories_by_keyword,
)
from app.schemas.long_term_memory import LongTermMemory


def _temp_db(tmp_path: Path) -> str:
    """创建临时数据库并返回路径，避免污染真实 data 目录。"""
    db_path = tmp_path / "companion.db"
    init_db(str(db_path))
    return str(db_path)


def _memory(content: str, importance: float = 0.5) -> LongTermMemory:
    """创建测试用长期记忆对象。"""
    return LongTermMemory(
        memory_type="preference",
        content=content,
        importance=importance,
        emotional_valence="neutral",
        source_text=content,
    )


def test_add_long_term_memory_can_save_memory(tmp_path: Path) -> None:
    """测试可以保存长期记忆并返回 id。"""
    db_path = _temp_db(tmp_path)

    memory_id = add_long_term_memory("user_a", _memory("用户喜欢听爵士乐"), db_path)

    assert memory_id > 0


def test_get_recent_memories_returns_latest_first(tmp_path: Path) -> None:
    """测试最近记忆按创建时间倒序返回。"""
    db_path = _temp_db(tmp_path)
    add_long_term_memory("user_a", _memory("第一条记忆"), db_path)
    add_long_term_memory("user_a", _memory("第二条记忆"), db_path)

    memories = get_recent_memories("user_a", limit=2, db_path=db_path)

    assert [memory.content for memory in memories] == ["第二条记忆", "第一条记忆"]


def test_get_important_memories_returns_high_importance_first(tmp_path: Path) -> None:
    """测试重要记忆按 importance 倒序返回。"""
    db_path = _temp_db(tmp_path)
    add_long_term_memory("user_a", _memory("普通偏好", importance=0.3), db_path)
    add_long_term_memory("user_a", _memory("重要经历", importance=0.9), db_path)

    memories = get_important_memories("user_a", limit=2, db_path=db_path)

    assert [memory.content for memory in memories] == ["重要经历", "普通偏好"]


def test_mark_memory_used_updates_last_used_at(tmp_path: Path) -> None:
    """测试标记记忆使用后会写入 last_used_at。"""
    db_path = _temp_db(tmp_path)
    memory_id = add_long_term_memory("user_a", _memory("用户怕突然很大的声音"), db_path)

    mark_memory_used(memory_id, db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT last_used_at FROM long_term_memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["last_used_at"] is not None


def test_search_memories_by_keyword_returns_matching_memory(tmp_path: Path) -> None:
    """测试关键词搜索可以返回内容匹配的记忆。"""
    db_path = _temp_db(tmp_path)
    add_long_term_memory("user_a", _memory("用户喜欢雨天散步", importance=0.7), db_path)
    add_long_term_memory("user_a", _memory("用户不喜欢太吵的环境", importance=0.9), db_path)

    memories = search_memories_by_keyword("user_a", "雨天", limit=5, db_path=db_path)

    assert [memory.content for memory in memories] == ["用户喜欢雨天散步"]
