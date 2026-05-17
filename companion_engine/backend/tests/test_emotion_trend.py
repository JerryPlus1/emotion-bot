"""情绪连续性追踪测试。"""

from pathlib import Path

from app.core.engine import handle_event
from app.db.init_db import init_db
from app.schemas.engine import EngineInput, SceneContext
from app.understanding.emotion_trace_store import (
    add_emotion_trace,
    get_recent_emotion_traces,
)
from app.understanding.emotion_trend import detect_emotion_trend


def _db_path(tmp_path: Path) -> str:
    """返回测试用临时数据库路径。"""
    return str(tmp_path / "companion.db")


def test_repeated_low_emotions_return_prolonged_low(tmp_path: Path) -> None:
    """测试连续低落情绪返回 prolonged_low。"""
    db_path = _db_path(tmp_path)
    init_db(db_path)
    add_emotion_trace("user_a", "sad", "none", db_path)
    add_emotion_trace("user_a", "anxious", "none", db_path)
    add_emotion_trace("user_a", "tired", "none", db_path)

    traces = get_recent_emotion_traces("user_a", 5, db_path)

    assert detect_emotion_trend(traces) == "prolonged_low"


def test_risk_increase_returns_worsening(tmp_path: Path) -> None:
    """测试风险升高返回 worsening。"""
    db_path = _db_path(tmp_path)
    init_db(db_path)
    add_emotion_trace("user_a", "sad", "none", db_path)
    add_emotion_trace("user_a", "sad", "medium", db_path)

    traces = get_recent_emotion_traces("user_a", 5, db_path)

    assert detect_emotion_trend(traces) == "worsening"


def test_emotion_getting_better_returns_improving(tmp_path: Path) -> None:
    """测试情绪从低落转好返回 improving。"""
    db_path = _db_path(tmp_path)
    init_db(db_path)
    add_emotion_trace("user_a", "sad", "none", db_path)
    add_emotion_trace("user_a", "neutral", "none", db_path)

    traces = get_recent_emotion_traces("user_a", 5, db_path)

    assert detect_emotion_trend(traces) == "improving"


def test_engine_debug_contains_emotion_trend(tmp_path: Path) -> None:
    """测试 engine debug 包含 emotion_trend。"""
    output = handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="我有点难过",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
    )

    assert "emotion_trend" in output.debug
