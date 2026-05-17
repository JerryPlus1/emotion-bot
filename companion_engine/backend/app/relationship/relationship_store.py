"""关系存储文件，负责保存和读取用户与机器人的关系状态。"""

from datetime import UTC, datetime

from app.db.connection import get_connection
from app.schemas.relationship import RelationshipState


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录关系状态更新时间。"""
    return datetime.now(UTC).isoformat()


def get_relationship_state(user_id: str, db_path: str) -> RelationshipState:
    """读取关系状态；如果数据库中没有记录，则返回默认状态。"""
    conn = get_connection(db_path)

    try:
        row = conn.execute(
            """
            SELECT
                user_id,
                relationship_stage,
                trust_level,
                intimacy_level,
                user_openness,
                recent_interaction_quality,
                last_meaningful_topic
            FROM relationship_state
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # 没有记录时使用 Schema 默认值，代表关系刚刚开始。
        return RelationshipState(user_id=user_id)

    return RelationshipState(
        user_id=row["user_id"],
        relationship_stage=row["relationship_stage"] or "stranger",
        trust_level=row["trust_level"] if row["trust_level"] is not None else 0.2,
        intimacy_level=row["intimacy_level"] if row["intimacy_level"] is not None else 0.1,
        user_openness=row["user_openness"] if row["user_openness"] is not None else 0.2,
        recent_interaction_quality=row["recent_interaction_quality"] or "neutral",
        last_meaningful_topic=row["last_meaningful_topic"],
    )


def save_relationship_state(state: RelationshipState, db_path: str) -> None:
    """保存关系状态；如果用户已有记录，则更新。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO relationship_state (
                user_id,
                relationship_stage,
                trust_level,
                intimacy_level,
                user_openness,
                recent_interaction_quality,
                last_meaningful_topic,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                relationship_stage = excluded.relationship_stage,
                trust_level = excluded.trust_level,
                intimacy_level = excluded.intimacy_level,
                user_openness = excluded.user_openness,
                recent_interaction_quality = excluded.recent_interaction_quality,
                last_meaningful_topic = excluded.last_meaningful_topic,
                updated_at = excluded.updated_at
            """,
            (
                state.user_id,
                state.relationship_stage,
                state.trust_level,
                state.intimacy_level,
                state.user_openness,
                state.recent_interaction_quality,
                state.last_meaningful_topic,
                _now_iso(),
            ),
        )

        # 提交关系状态保存事务，确保下一次读取拿到最新阶段。
        conn.commit()
    finally:
        conn.close()
