"""短期对话记忆存储，记录最近几轮对话用于重复控制。"""

from datetime import UTC, datetime

from app.db.connection import get_connection


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录短期对话时间。"""
    return datetime.now(UTC).isoformat()


def add_dialogue_turn(
    user_id: str,
    role: str,
    content: str,
    strategy: str | None,
    db_path: str,
) -> None:
    """新增一条短期对话轮次。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO short_term_dialogue (
                user_id,
                role,
                content,
                strategy,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, role, content, strategy, _now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_dialogue(user_id: str, limit: int, db_path: str) -> list[dict]:
    """读取最近的短期对话，按时间从旧到新返回。"""
    conn = get_connection(db_path)

    try:
        rows = conn.execute(
            """
            SELECT id, user_id, role, content, strategy, created_at
            FROM short_term_dialogue
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "role": row["role"],
            "content": row["content"],
            "strategy": row["strategy"],
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]


def get_recent_bot_messages(user_id: str, limit: int, db_path: str) -> list[str]:
    """读取最近机器人回复文本，按时间从旧到新返回。"""
    dialogue = get_recent_dialogue(user_id, limit * 2, db_path)
    bot_messages = [turn["content"] for turn in dialogue if turn["role"] == "assistant"]
    return bot_messages[-limit:]


def clear_short_term_dialogue(user_id: str, db_path: str) -> None:
    """清空指定用户的短期对话记忆。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            "DELETE FROM short_term_dialogue WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()
