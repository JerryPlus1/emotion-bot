"""主动互动存储文件，负责记录和查询主动说话决策历史。"""

from datetime import UTC, datetime, timedelta

from app.db.connection import get_connection


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录主动决策时间。"""
    return datetime.now(UTC).isoformat()


def log_proactive_decision(
    user_id: str,
    event_type: str,
    should_speak: bool,
    proactive_type: str | None,
    question_type: str | None,
    reason: str,
    db_path: str,
) -> None:
    """记录一次主动说话判断结果。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO proactive_logs (
                user_id,
                event_type,
                should_speak,
                proactive_type,
                question_type,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                event_type,
                1 if should_speak else 0,
                proactive_type,
                question_type,
                reason,
                _now_iso(),
            ),
        )

        # 提交日志，供冷却策略和后续分析使用。
        conn.commit()
    finally:
        conn.close()


def count_recent_proactive(user_id: str, minutes: int, db_path: str) -> int:
    """统计最近指定分钟内机器人主动开口的次数。"""
    cutoff_time = datetime.now(UTC) - timedelta(minutes=minutes)
    conn = get_connection(db_path)

    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM proactive_logs
            WHERE user_id = ?
              AND should_speak = 1
              AND created_at >= ?
            """,
            (user_id, cutoff_time.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    return int(row["count"])


def get_last_rejection_time(user_id: str, db_path: str) -> str | None:
    """读取最近一次用户拒绝或不愿意互动相关记录的时间。"""
    conn = get_connection(db_path)

    try:
        row = conn.execute(
            """
            SELECT created_at
            FROM proactive_logs
            WHERE user_id = ?
              AND (
                reason LIKE '%rejection%'
                OR reason LIKE '%user_unwilling%'
              )
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return row["created_at"]
