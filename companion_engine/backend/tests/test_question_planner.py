"""主动问题规划测试，验证轻量问题和主动互动类型选择规则。"""

from app.proactive.proactive_dialogue_planner import choose_proactive_type
from app.proactive.question_planner import choose_question_type
from app.schemas.emotion import ConversationIntent, EmotionType
from app.schemas.engine import DialogueContext, SceneContext
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState


def _context() -> DialogueContext:
    """创建主动规划测试用上下文。"""
    return DialogueContext(
        user_id="user_a",
        event_type="timer_event",
        user_text=None,
        scene=SceneContext(time="10:00", is_user_nearby=True),
    )


def test_negative_emotion_asks_no_question() -> None:
    """测试情绪差时不问偏好问题。"""
    question_type = choose_question_type(
        UserProfile(user_id="user_a"),
        PersonaSnapshot(),
        RelationshipState(user_id="user_a"),
        ConversationIntent.casual_chat,
        EmotionType.sad,
    )

    assert question_type == "none"


def test_wants_space_asks_no_question() -> None:
    """测试用户想要空间时不问问题。"""
    question_type = choose_question_type(
        UserProfile(user_id="user_a"),
        PersonaSnapshot(),
        RelationshipState(user_id="user_a"),
        ConversationIntent.wants_space,
        EmotionType.neutral,
    )

    assert question_type == "none"


def test_missing_profile_asks_profile_question() -> None:
    """测试缺少用户支持偏好时优先问画像问题。"""
    question_type = choose_question_type(
        UserProfile(user_id="user_a", preferred_support_style="unknown"),
        PersonaSnapshot(),
        RelationshipState(user_id="user_a", relationship_stage="stranger"),
        ConversationIntent.casual_chat,
        EmotionType.neutral,
    )

    assert question_type == "profile_question"


def test_familiar_relationship_can_ask_persona_question() -> None:
    """测试关系熟悉后可以询问 Persona 偏好问题。"""
    question_type = choose_question_type(
        UserProfile(user_id="user_a", preferred_support_style="listen_first"),
        PersonaSnapshot(warmth_level="medium"),
        RelationshipState(user_id="user_a", relationship_stage="familiar"),
        ConversationIntent.casual_chat,
        EmotionType.neutral,
    )

    assert question_type == "persona_question"


def test_low_initiative_tolerance_uses_quiet_company() -> None:
    """测试低主动容忍时主动类型为 quiet_company。"""
    proactive_type = choose_proactive_type(
        _context(),
        UserProfile(user_id="user_a", initiative_tolerance="low"),
        RelationshipState(user_id="user_a", relationship_stage="familiar"),
        "none",
    )

    assert proactive_type == "quiet_company"


def test_stranger_defaults_to_soft_greeting() -> None:
    """测试陌生关系默认使用 soft_greeting。"""
    proactive_type = choose_proactive_type(
        _context(),
        UserProfile(user_id="user_a"),
        RelationshipState(user_id="user_a", relationship_stage="stranger"),
        "none",
    )

    assert proactive_type == "soft_greeting"


def test_trusted_defaults_to_memory_recall() -> None:
    """测试 trusted 关系默认使用 memory_recall。"""
    proactive_type = choose_proactive_type(
        _context(),
        UserProfile(user_id="user_a"),
        RelationshipState(user_id="user_a", relationship_stage="trusted"),
        "none",
    )

    assert proactive_type == "memory_recall"
