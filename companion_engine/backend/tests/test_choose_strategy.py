"""回复策略选择测试，验证规则优先级和 Enum 兼容。"""

from app.schemas.emotion import ConversationIntent, EmotionType, RiskLevel
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState
from app.schemas.strategy import EmpathyStrategy
from app.strategy.choose_strategy import choose_strategy


def _choose(
    intent: object = ConversationIntent.casual_chat,
    emotion: object = EmotionType.neutral,
    risk_level: object = RiskLevel.none,
    proactive_type: object | None = None,
    question_type: object | None = None,
) -> EmpathyStrategy:
    """创建默认依赖，便于聚焦测试单条策略规则。"""
    return choose_strategy(
        intent=intent,
        emotion=emotion,
        risk_level=risk_level,
        proactive_type=proactive_type,
        question_type=question_type,
        user_profile=UserProfile(user_id="user_a"),
        persona=PersonaSnapshot(),
        relationship_state=RelationshipState(user_id="user_a"),
    )


def test_high_risk_returns_crisis_redirect() -> None:
    """测试高风险返回危机引导策略。"""
    assert _choose(risk_level=RiskLevel.high) == EmpathyStrategy.crisis_redirect


def test_medium_risk_returns_crisis_redirect() -> None:
    """测试中风险返回危机引导策略。"""
    assert _choose(risk_level="medium") == EmpathyStrategy.crisis_redirect


def test_wants_space_returns_quiet_company() -> None:
    """测试用户想要空间时返回安静陪伴。"""
    assert _choose(intent=ConversationIntent.wants_space) == EmpathyStrategy.quiet_company


def test_tired_returns_quiet_company() -> None:
    """测试疲惫情绪返回安静陪伴。"""
    assert _choose(emotion=EmotionType.tired) == EmpathyStrategy.quiet_company


def test_sad_returns_emotional_validation() -> None:
    """测试难过情绪返回情绪确认。"""
    assert _choose(emotion=EmotionType.sad) == EmpathyStrategy.emotional_validation


def test_anxious_returns_choice_offering() -> None:
    """测试焦虑情绪返回选择提供。"""
    assert _choose(emotion=EmotionType.anxious) == EmpathyStrategy.choice_offering


def test_profile_question_returns_profile_question() -> None:
    """测试画像问题类型返回画像问题策略。"""
    assert _choose(question_type="profile_question") == EmpathyStrategy.profile_question


def test_persona_question_returns_persona_question() -> None:
    """测试人格问题类型返回人格问题策略。"""
    assert _choose(question_type="persona_question") == EmpathyStrategy.persona_question


def test_playful_returns_playful_response() -> None:
    """测试 playful 意图返回轻松回应。"""
    assert _choose(intent=ConversationIntent.playful) == EmpathyStrategy.playful_response


def test_soft_greeting_returns_soft_greeting() -> None:
    """测试 soft_greeting 主动类型返回轻柔问候。"""
    assert _choose(proactive_type="soft_greeting") == EmpathyStrategy.soft_greeting
