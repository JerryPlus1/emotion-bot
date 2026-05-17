"""Persona 存储测试，验证稳定风格和偏好证据的保存规则。"""

from pathlib import Path

from app.db.connection import get_connection
from app.db.init_db import init_db
from app.persona.persona_store import (
    apply_persona_updates,
    get_current_persona,
    save_persona_preferences,
)
from app.schemas.persona import PersonaSnapshot, PersonaUpdate


def _temp_db(tmp_path: Path) -> str:
    """创建临时数据库并返回路径，避免污染真实 data 目录。"""
    db_path = tmp_path / "companion.db"
    init_db(str(db_path))
    return str(db_path)


def test_get_current_persona_returns_default_persona(tmp_path: Path) -> None:
    """测试没有数据库记录时可以读取默认 Persona。"""
    db_path = _temp_db(tmp_path)

    persona = get_current_persona("user_a", db_path)

    assert persona == PersonaSnapshot()


def test_save_persona_preferences_records_evidence(tmp_path: Path) -> None:
    """测试 PersonaUpdate 会写入偏好证据表。"""
    db_path = _temp_db(tmp_path)
    updates = [
        PersonaUpdate(
            dimension="warmth_level",
            value="high",
            confidence=0.5,
            evidence="你可以温柔一点。",
            source_type="explicit_feedback",
        )
    ]

    save_persona_preferences("user_a", updates, db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT user_id, dimension, value, confidence, evidence, source_type FROM persona_preferences"
        ).fetchone()
    finally:
        conn.close()

    assert row["user_id"] == "user_a"
    assert row["dimension"] == "warmth_level"
    assert row["value"] == "high"
    assert row["confidence"] == 0.5
    assert row["evidence"] == "你可以温柔一点。"
    assert row["source_type"] == "explicit_feedback"


def test_high_confidence_update_changes_persona(tmp_path: Path) -> None:
    """测试高置信度更新可以修改稳定 Persona。"""
    db_path = _temp_db(tmp_path)
    updates = [
        PersonaUpdate(
            dimension="playfulness_level",
            value="high",
            confidence=0.8,
            evidence="用户多次喜欢轻松玩笑。",
            source_type="observation",
        )
    ]

    persona = apply_persona_updates("user_a", updates, db_path)

    assert persona.playfulness_level == "high"


def test_low_confidence_update_does_not_change_persona(tmp_path: Path) -> None:
    """测试低置信度更新不会修改稳定 Persona。"""
    db_path = _temp_db(tmp_path)
    updates = [
        PersonaUpdate(
            dimension="analysis_level",
            value="high",
            confidence=0.5,
            evidence="可能喜欢详细分析。",
            source_type="observation",
        )
    ]

    persona = apply_persona_updates("user_a", updates, db_path)

    assert persona.analysis_level == "medium"


def test_explicit_feedback_with_medium_confidence_changes_persona(tmp_path: Path) -> None:
    """测试明确反馈在 confidence >= 0.6 时可以修改稳定 Persona。"""
    db_path = _temp_db(tmp_path)
    updates = [
        PersonaUpdate(
            dimension="speech_length",
            value="short",
            confidence=0.6,
            evidence="以后回答短一点。",
            source_type="explicit_feedback",
        )
    ]

    persona = apply_persona_updates("user_a", updates, db_path)

    assert persona.speech_length == "short"


def test_unknown_dimension_does_not_change_persona(tmp_path: Path) -> None:
    """测试不存在的维度不会修改稳定 Persona。"""
    db_path = _temp_db(tmp_path)
    updates = [
        PersonaUpdate(
            dimension="unknown_dimension",
            value="anything",
            confidence=0.95,
            evidence="未知维度测试。",
            source_type="explicit_feedback",
        )
    ]

    persona = apply_persona_updates("user_a", updates, db_path)

    assert persona == PersonaSnapshot()
