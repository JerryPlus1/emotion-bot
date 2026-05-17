"""长期记忆存储文件，负责保存、读取和标记使用长期记忆。"""

from datetime import UTC, datetime
from typing import Any

from app.db.connection import get_connection
from app.schemas.long_term_memory import LongTermMemory


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录记忆创建和使用时间。"""
    return datetime.now(UTC).isoformat()


def _memory_from_row(row: Any) -> LongTermMemory:
    """把数据库查询结果转换为 LongTermMemory。"""
    return LongTermMemory(
        memory_type=row["memory_type"],
        content=row["content"],
        importance=row["importance"],
        emotional_valence=row["emotional_valence"] or "neutral",
        source_text=row["source_text"],
    )


def add_long_term_memory(
    user_id: str,
    memory: LongTermMemory,
    db_path: str,
) -> int:
    """新增一条长期记忆，并返回数据库生成的记忆 id。"""
    conn = get_connection(db_path)

    try:
        cursor = conn.execute(
            """
            INSERT INTO long_term_memories (
                user_id,
                memory_type,
                content,
                importance,
                emotional_valence,
                source_text,
                created_at,
                last_used_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                memory.memory_type,
                memory.content,
                memory.importance,
                memory.emotional_valence,
                memory.source_text,
                _now_iso(),
                None,
            ),
        )

        # 提交新增事务，让返回的 id 对后续读取立即可见。
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()

def get_recent_memories(
    user_id: str,
    limit: int = 5,
    db_path: str = "../data/companion.db",
) -> list[LongTermMemory]:
    """按创建时间倒序读取最近的长期记忆。"""
    conn = get_connection(db_path)

    try:
        rows = conn.execute(
            """
            SELECT memory_type, content, importance, emotional_valence, source_text
            FROM long_term_memories
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    return [_memory_from_row(row) for row in rows]

def get_important_memories(
    user_id: str,
    limit: int = 5,
    db_path: str = "../data/companion.db",
) -> list[LongTermMemory]:
    """按重要度倒序读取长期记忆。"""
    conn = get_connection(db_path)

    try:
        rows = conn.execute(
            """
            SELECT memory_type, content, importance, emotional_valence, source_text
            FROM long_term_memories
            WHERE user_id = ?
            ORDER BY importance DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    return [_memory_from_row(row) for row in rows]


def mark_memory_used(memory_id: int, db_path: str) -> None:
    """标记一条长期记忆已被使用，更新 last_used_at。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            UPDATE long_term_memories
            SET last_used_at = ?
            WHERE id = ?
            """,
            (_now_iso(), memory_id),
        )

        # 提交使用时间更新，方便后续记忆选择模块参考。
        conn.commit()
    finally:
        conn.close()


def search_memories_by_keyword(
    user_id: str,
    keyword: str,
    limit: int = 5,
    db_path: str = "../data/companion.db",
) -> list[LongTermMemory]:
    """使用 SQL LIKE 对记忆内容做简单关键词搜索。"""
    conn = get_connection(db_path)

    try:
        rows = conn.execute(
            """
            SELECT memory_type, content, importance, emotional_valence, source_text
            FROM long_term_memories
            WHERE user_id = ?
              AND content LIKE ?
            ORDER BY importance DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, f"%{keyword}%", limit),
        ).fetchall()
    finally:
        conn.close()

    return [_memory_from_row(row) for row in rows]
