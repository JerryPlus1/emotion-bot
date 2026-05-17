"""反馈存储文件，负责保存用户反应评估结果。"""

from datetime import UTC, datetime

from app.db.connection import get_connection


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录反馈创建时间。"""
    return datetime.now(UTC).isoformat()


def save_interaction_feedback(
    user_id: str,
    robot_response: str,
    user_reaction: str | None,
    quality_score: float,
    feedback_type: str,
    db_path: str,
) -> None:
    """保存一次用户反应评估结果。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO interaction_feedback (
                user_id,
                robot_response,
                user_reaction,
                quality_score,
                feedback_type,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                robot_response,
                user_reaction,
                quality_score,
                feedback_type,
                _now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
