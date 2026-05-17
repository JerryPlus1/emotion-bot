"""主动说话判断测试，验证冷却、时间和用户容忍度规则。"""

from pathlib import Path

from app.db.init_db import init_db
from app.proactive.proactive_store import log_proactive_decision
from app.proactive.should_speak import should_speak
from app.schemas.engine import DialogueContext, SceneContext
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState


def _temp_db(tmp_path: Path) -> str:
    """创建临时数据库并返回路径，避免污染真实 data 目录。"""
    db_path = tmp_path / "companion.db"
    init_db(str(db_path))
    return str(db_path)


def _context(
    event_type: str = "ambient_event",
    scene_time: str | None = "10:00",
    is_user_nearby: bool = True,
) -> DialogueContext:
    """创建主动说话测试用上下文。"""
    return DialogueContext(
        user_id="user_a",
        event_type=event_type,
        user_text=None,
        scene=SceneContext(time=scene_time, is_user_nearby=is_user_nearby),
    )


def _dependencies() -> tuple[UserProfile, PersonaSnapshot, RelationshipState]:
    """创建主动判断所需的默认依赖对象。"""
    return (
        UserProfile(user_id="user_a"),
        PersonaSnapshot(),
        RelationshipState(user_id="user_a"),
    )


def test_user_direct_chat_always_should_speak(tmp_path: Path) -> None:
    """测试用户主动聊天时机器人一定回应。"""
    db_path = _temp_db(tmp_path)
    profile, persona, relationship = _dependencies()

    result = should_speak(_context(event_type="user_direct_chat"), profile, persona, relationship, db_path)

    assert result == (True, "user_initiated")


def test_cooldown_returns_false(tmp_path: Path) -> None:
    """测试冷却中不主动说话。"""
    db_path = _temp_db(tmp_path)
    profile, persona, relationship = _dependencies()
    log_proactive_decision("user_a", "ambient_event", True, None, None, "allowed", db_path)
    log_proactive_decision("user_a", "timer_event", True, None, None, "allowed", db_path)

    result = should_speak(_context(event_type="timer_event"), profile, persona, relationship, db_path)

    assert result == (False, "cooldown")


def test_low_initiative_tolerance_blocks_normal_event(tmp_path: Path) -> None:
    """测试用户低主动容忍时普通主动事件不说话。"""
    db_path = _temp_db(tmp_path)
    profile = UserProfile(user_id="user_a", initiative_tolerance="low")
    persona = PersonaSnapshot()
    relationship = RelationshipState(user_id="user_a")

    result = should_speak(_context(event_type="timer_event"), profile, persona, relationship, db_path)

    assert result == (False, "low_initiative_tolerance")


def test_night_quiet_blocks_proactive_speech(tmp_path: Path) -> None:
    """测试夜间安静时段不主动说话。"""
    db_path = _temp_db(tmp_path)
    profile, persona, relationship = _dependencies()

    result = should_speak(_context(scene_time="02:30"), profile, persona, relationship, db_path)

    assert result == (False, "night_quiet")


def test_user_not_nearby_blocks_ambient_event(tmp_path: Path) -> None:
    """测试用户不在附近时 ambient_event 不主动说话。"""
    db_path = _temp_db(tmp_path)
    profile, persona, relationship = _dependencies()

    result = should_speak(
        _context(event_type="ambient_event", is_user_nearby=False),
        profile,
        persona,
        relationship,
        db_path,
    )

    assert result == (False, "user_not_nearby")


def test_allowed_case_returns_true(tmp_path: Path) -> None:
    """测试满足条件时允许主动说话。"""
    db_path = _temp_db(tmp_path)
    profile, persona, relationship = _dependencies()

    result = should_speak(_context(event_type="timer_event"), profile, persona, relationship, db_path)

    assert result == (True, "allowed")
