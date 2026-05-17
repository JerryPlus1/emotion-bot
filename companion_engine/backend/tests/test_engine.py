"""对话引擎主流程测试，验证第 12 阶段端到端 Mock 流程。"""

from pathlib import Path

from app.core.engine import handle_event
from app.memory.profile_store import get_profile
from app.persona.persona_store import get_current_persona
from app.schemas.engine import EngineInput, SceneContext


def _db_path(tmp_path: Path) -> str:
    """返回测试用临时数据库路径，避免污染真实 data 目录。"""
    return str(tmp_path / "companion.db")


def test_user_direct_chat_returns_response(tmp_path: Path) -> None:
    """测试用户主动聊天会返回 should_speak=True 和回复文本。"""
    output = handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="你好呀",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
    )

    assert output.should_speak is True
    assert output.response_text


def test_night_proactive_event_should_not_speak(tmp_path: Path) -> None:
    """测试夜间主动事件不会主动说话。"""
    output = handle_event(
        EngineInput(
            event_type="ambient_event",
            user_text=None,
            scene=SceneContext(time="02:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
    )

    assert output.should_speak is False
    assert output.response_text is None
    assert output.debug["speak_reason"] == "night_quiet"


def test_high_risk_uses_crisis_redirect(tmp_path: Path) -> None:
    """测试高风险输入必须使用 crisis_redirect。"""
    output = handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="我不想活了",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
    )

    assert output.should_speak is True
    assert output.risk_level == "high"
    assert output.strategy == "crisis_redirect"
    assert "紧急救援" in output.response_text


def test_memory_update_disliked_responses(tmp_path: Path) -> None:
    """测试用户说别分析后会更新画像 disliked_responses。"""
    db_path = _db_path(tmp_path)

    handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="别分析了，我就想吐槽",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        db_path,
    )
    profile = get_profile("default_user", db_path)

    assert "过早分析" in profile.disliked_responses


def test_persona_update_warmth_level(tmp_path: Path) -> None:
    """测试用户要求温柔一点后会更新 Persona warmth_level。"""
    db_path = _db_path(tmp_path)

    handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="你能不能温柔一点",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        db_path,
    )
    persona = get_current_persona("default_user", db_path)

    assert persona.warmth_level == "high"


def test_hardware_actions_are_returned(tmp_path: Path) -> None:
    """测试引擎输出中包含硬件动作。"""
    output = handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="哈哈开个玩笑",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
    )

    assert output.hardware_actions is not None
    assert output.hardware_actions.speech_text == output.response_text
