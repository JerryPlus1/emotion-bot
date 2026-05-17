"""人格存储文件，负责保存、读取和更新机器人长期说话风格。"""

from datetime import UTC, datetime

from app.db.connection import get_connection
from app.persona.persona_policy import should_apply_persona_update
from app.schemas.persona import PersonaSnapshot, PersonaUpdate


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录人格更新时间。"""
    return datetime.now(UTC).isoformat()


def get_current_persona(user_id: str, db_path: str) -> PersonaSnapshot:
    """读取当前稳定 Persona；如果不存在记录，则返回默认 Persona。"""
    conn = get_connection(db_path)

    try:
        row = conn.execute(
            """
            SELECT
                role_style,
                warmth_level,
                initiative_level,
                analysis_level,
                playfulness_level,
                speech_length,
                companionship_style
            FROM persona_state
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # 没有保存过 Persona 时使用 Schema 默认风格。
        return PersonaSnapshot()

    return PersonaSnapshot(
        role_style=row["role_style"] or "soft_companion",
        warmth_level=row["warmth_level"] or "medium",
        initiative_level=row["initiative_level"] or "medium",
        analysis_level=row["analysis_level"] or "medium",
        playfulness_level=row["playfulness_level"] or "medium",
        speech_length=row["speech_length"] or "medium",
        companionship_style=row["companionship_style"] or "listen_first",
    )


def save_persona(user_id: str, persona: PersonaSnapshot, db_path: str) -> None:
    """保存当前稳定 Persona；如果用户已有记录，则更新。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO persona_state (
                user_id,
                role_style,
                warmth_level,
                initiative_level,
                analysis_level,
                playfulness_level,
                speech_length,
                companionship_style,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                role_style = excluded.role_style,
                warmth_level = excluded.warmth_level,
                initiative_level = excluded.initiative_level,
                analysis_level = excluded.analysis_level,
                playfulness_level = excluded.playfulness_level,
                speech_length = excluded.speech_length,
                companionship_style = excluded.companionship_style,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                persona.role_style,
                persona.warmth_level,
                persona.initiative_level,
                persona.analysis_level,
                persona.playfulness_level,
                persona.speech_length,
                persona.companionship_style,
                _now_iso(),
            ),
        )

        # 提交稳定 Persona 保存事务。
        conn.commit()
    finally:
        conn.close()


def save_persona_preferences(
    user_id: str,
    updates: list[PersonaUpdate],
    db_path: str,
) -> None:
    """保存人格偏好证据，即使它们暂时不会修改稳定 Persona。"""
    conn = get_connection(db_path)

    try:
        conn.executemany(
            """
            INSERT INTO persona_preferences (
                user_id,
                dimension,
                value,
                confidence,
                evidence,
                source_type,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    update.dimension,
                    update.value,
                    update.confidence,
                    update.evidence,
                    update.source_type,
                    _now_iso(),
                )
                for update in updates
            ],
        )

        # 提交偏好证据，保留后续分析和回放的依据。
        conn.commit()
    finally:
        conn.close()


def apply_persona_updates(
    user_id: str,
    updates: list[PersonaUpdate],
    db_path: str,
) -> PersonaSnapshot:
    """保存人格更新证据，并按规则合并到稳定 Persona。"""
    persona = get_current_persona(user_id, db_path)
    save_persona_preferences(user_id, updates, db_path)

    for update in updates:
        if not should_apply_persona_update(update):
            continue

        # 策略层已确认字段存在，这里仍用 hasattr 保持存储层稳健。
        if hasattr(persona, update.dimension):
            setattr(persona, update.dimension, update.value)

    save_persona(user_id, persona, db_path)
    return persona
