"""情绪轨迹存储，用于记录用户最近情绪和风险变化。"""

from datetime import UTC, datetime
from typing import Any

from app.db.connection import get_connection


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录情绪轨迹时间。"""
    return datetime.now(UTC).isoformat()


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出文本值。"""
    return getattr(value, "value", value)


def add_emotion_trace(
    user_id: str,
    emotion: Any,
    risk_level: Any,
    db_path: str,
) -> None:
    """新增一条情绪轨迹记录。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO emotion_traces (
                user_id,
                emotion,
                risk_level,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, _as_value(emotion), _as_value(risk_level), _now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_emotion_traces(user_id: str, limit: int, db_path: str) -> list[dict]:
    """读取最近情绪轨迹，按时间从旧到新返回。"""
    conn = get_connection(db_path)

    try:
        rows = conn.execute(
            """
            SELECT id, user_id, emotion, risk_level, created_at
            FROM emotion_traces
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
            "emotion": row["emotion"],
            "risk_level": row["risk_level"],
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]
