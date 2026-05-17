"""核心 Schema 测试，确保第 1 阶段数据结构和校验规则可用。"""

import pytest
from pydantic import ValidationError

from app.schemas.engine import EngineInput, SceneContext
from app.schemas.memory import MemoryUpdate
from app.schemas.persona import PersonaUpdate
from app.schemas.relationship import RelationshipState


def test_engine_input_can_be_created() -> None:
    """测试 EngineInput 可以用最小必要字段创建。"""
    engine_input = EngineInput(event_type="user_message", user_text="你好", scene=SceneContext())

    assert engine_input.user_id == "default_user"
    assert engine_input.scene.is_user_nearby is False


def test_memory_update_can_be_created() -> None:
    """测试 MemoryUpdate 可以创建，并接受 0 到 1 范围内的可信度。"""
    memory_update = MemoryUpdate(
        key="liked_topics",
        value=["音乐", "散步"],
        confidence=0.8,
        source_text="我最近喜欢听音乐和散步。",
    )

    assert memory_update.confidence == 0.8


def test_persona_update_can_be_created() -> None:
    """测试 PersonaUpdate 可以创建。"""
    persona_update = PersonaUpdate(
        dimension="warmth_level",
        value="high",
        confidence=0.9,
        evidence="你可以更温柔一点。",
        source_type="user_feedback",
    )

    assert persona_update.dimension == "warmth_level"


def test_relationship_state_can_be_created() -> None:
    """测试 RelationshipState 可以创建，并使用默认关系数值。"""
    relationship_state = RelationshipState(user_id="default_user")

    assert relationship_state.trust_level == 0.2
    assert relationship_state.intimacy_level == 0.1


def test_confidence_greater_than_one_raises_error() -> None:
    """测试 confidence 超过 1 会触发校验错误。"""
    with pytest.raises(ValidationError):
        MemoryUpdate(
            key="preferred_support_style",
            value="listen_first",
            confidence=1.1,
            source_text="先听我说完就好。",
        )


def test_trust_level_less_than_zero_raises_error() -> None:
    """测试 trust_level 小于 0 会触发校验错误。"""
    with pytest.raises(ValidationError):
        RelationshipState(user_id="default_user", trust_level=-0.1)
