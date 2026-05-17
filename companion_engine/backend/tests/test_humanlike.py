"""极致真人感系统测试，验证沉默、提问节流、分寸和安全优先。"""

from app.humanlike.humanlike_controller import make_reply_humanlike
from app.humanlike.memory_recall_policy import rewrite_memory_reference
from app.schemas.emotion import ConversationIntent, EmotionType, RiskLevel
from app.schemas.long_term_memory import LongTermMemory
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState
from app.schemas.strategy import EmpathyStrategy
from app.safety.crisis_policy import get_crisis_response


def _profile(**kwargs) -> UserProfile:
    """创建测试用用户画像。"""
    return UserProfile(user_id="user_a", **kwargs)


def _persona(**kwargs) -> PersonaSnapshot:
    """创建测试用 Persona。"""
    return PersonaSnapshot(**kwargs)


def _relationship(stage: str = "familiar", **kwargs) -> RelationshipState:
    """创建测试用关系状态。"""
    return RelationshipState(user_id="user_a", relationship_stage=stage, **kwargs)


def _memory(content: str) -> LongTermMemory:
    """创建测试用长期记忆。"""
    return LongTermMemory(
        memory_type="preference",
        content=content,
        importance=0.8,
        emotional_valence="warm",
        source_text=content,
    )


def test_wants_space_returns_silence_reply() -> None:
    """测试 wants_space 时返回沉默陪伴。"""
    reply = make_reply_humanlike(
        raw_reply="你要不要说说发生了什么？",
        intent=ConversationIntent.wants_space,
        emotion=EmotionType.neutral,
        risk_level=RiskLevel.none,
        strategy=EmpathyStrategy.quiet_company,
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("trusted"),
        memories=[],
        recent_bot_messages=[],
    )

    assert reply == "好，我懂。今天就不追着你说了，我在。"


def test_customer_service_tone_is_removed() -> None:
    """测试客服腔会被删除或替换。"""
    reply = make_reply_humanlike(
        raw_reply="很高兴为您服务。我理解您的感受。请问还有什么可以帮您？",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="emotional_validation",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship(),
        memories=[],
        recent_bot_messages=[],
    )

    assert "很高兴为您服务" not in reply
    assert "请问还有什么可以帮您" not in reply
    assert "听起来真的不太好受" in reply


def test_recent_many_questions_removes_new_questions() -> None:
    """测试最近多次追问后，新回复不再追问。"""
    reply = make_reply_humanlike(
        raw_reply="我在这儿。你想说说吗？要不要我帮你想？",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="emotional_validation",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship(),
        memories=[],
        recent_bot_messages=["你还好吗？", "想聊聊吗？", "我在。"],
    )

    assert "？" not in reply


def test_stranger_removes_too_intimate_language() -> None:
    """测试 stranger 阶段不会出现过度亲密语言。"""
    reply = make_reply_humanlike(
        raw_reply="抱抱你，我一直都在，靠着我就好。",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="emotional_validation",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("stranger"),
        memories=[],
        recent_bot_messages=[],
    )

    assert "抱抱你" not in reply
    assert "我一直都在" not in reply
    assert "靠着我" not in reply


def test_close_friend_can_be_naturally_close() -> None:
    """测试 close_friend 阶段可以更自然亲近。"""
    reply = make_reply_humanlike(
        raw_reply="嗯，不问了。你靠一会儿就好，我在呢。",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="quiet_company",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("close_friend"),
        memories=[],
        recent_bot_messages=[],
    )

    assert "你靠一会儿就好" in reply


def test_low_analysis_persona_reduces_analysis_sentence() -> None:
    """测试 low analysis persona 会减少分析句。"""
    reply = make_reply_humanlike(
        raw_reply="原因可能是你最近太累了。先慢一点。我在。",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="emotional_validation",
        user_profile=_profile(),
        persona=_persona(analysis_level="low"),
        relationship_state=_relationship(),
        memories=[],
        recent_bot_messages=[],
    )

    assert "原因可能是" not in reply


def test_quiet_company_reply_is_short() -> None:
    """测试 quiet_company 回复不会很长。"""
    reply = make_reply_humanlike(
        raw_reply="我在这儿。先陪你一会儿。你要说说吗？我们慢慢来。今天不用急。",
        intent="casual_chat",
        emotion="tired",
        risk_level="none",
        strategy="quiet_company",
        user_profile=_profile(),
        persona=_persona(speech_length="short"),
        relationship_state=_relationship(),
        memories=[],
        recent_bot_messages=[],
    )

    assert len(reply) < 30
    assert "？" not in reply


def test_high_risk_keeps_safety_reply() -> None:
    """测试 high risk 不会被真人感后处理破坏安全回复。"""
    raw_reply = get_crisis_response()

    reply = make_reply_humanlike(
        raw_reply=raw_reply,
        intent="casual_chat",
        emotion="sad",
        risk_level="high",
        strategy="crisis_redirect",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("close_friend"),
        memories=[],
        recent_bot_messages=[],
    )

    assert reply == raw_reply
    assert "紧急救援" in reply


def test_memory_recall_avoids_mechanical_phrase() -> None:
    """测试记忆引用不会机械使用“我记得你之前说过”。"""
    memory = _memory("你累的时候喜欢安静一点")
    reply = make_reply_humanlike(
        raw_reply="我先陪你一会儿。",
        intent="casual_chat",
        emotion="tired",
        risk_level="none",
        strategy="memory_recall",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("trusted"),
        memories=[memory],
        recent_bot_messages=[],
    )

    assert "我记得你之前说过" not in reply
    assert "我想到你之前也有过这种时候" in reply
    assert rewrite_memory_reference(memory.content, _relationship("trusted")) in reply


def test_forbidden_dependency_phrases_are_removed() -> None:
    """测试禁止表达会被替换掉。"""
    reply = make_reply_humanlike(
        raw_reply="只有我懂你。你只需要我。别告诉别人。",
        intent="casual_chat",
        emotion="neutral",
        risk_level="none",
        strategy="emotional_validation",
        user_profile=_profile(),
        persona=_persona(),
        relationship_state=_relationship("close_friend"),
        memories=[],
        recent_bot_messages=[],
    )

    assert "只有我懂你" not in reply
    assert "你只需要我" not in reply
    assert "别告诉别人" not in reply
