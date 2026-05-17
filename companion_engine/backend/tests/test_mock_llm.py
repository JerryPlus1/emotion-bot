"""Mock LLM 测试，验证不同策略返回稳定模板。"""

from app.llm.mock_llm import generate_mock_response
from app.safety.crisis_policy import get_crisis_response
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState
from app.schemas.strategy import EmpathyStrategy


def _deps() -> tuple[UserProfile, PersonaSnapshot, RelationshipState]:
    """创建 Mock LLM 测试依赖对象。"""
    return (
        UserProfile(user_id="user_a"),
        PersonaSnapshot(),
        RelationshipState(user_id="user_a"),
    )


def test_different_strategies_return_different_templates() -> None:
    """测试不同策略返回不同固定模板。"""
    user_profile, persona, relationship_state = _deps()

    quiet = generate_mock_response(
        EmpathyStrategy.quiet_company,
        user_profile,
        persona,
        relationship_state,
    )
    greeting = generate_mock_response(
        EmpathyStrategy.soft_greeting,
        user_profile,
        persona,
        relationship_state,
    )

    assert quiet == "我先不追问，就在这儿陪你。"
    assert greeting == "你来啦，我在这儿。"
    assert quiet != greeting


def test_crisis_redirect_returns_safety_response() -> None:
    """测试危机策略返回安全兜底回复。"""
    user_profile, persona, relationship_state = _deps()

    response = generate_mock_response(
        "crisis_redirect",
        user_profile,
        persona,
        relationship_state,
    )

    assert response == get_crisis_response()
    assert "紧急救援" in response


def test_user_text_can_make_fallback_contextual() -> None:
    """测试 fallback 会优先贴合用户本轮原话。"""
    user_profile, persona, relationship_state = _deps()

    response = generate_mock_response(
        EmpathyStrategy.profile_question,
        user_profile,
        persona,
        relationship_state,
        user_text="我想去唱歌",
    )

    assert response == "好啊，去唱吧。等你唱完回来，我想听听你唱得开不开心。"
