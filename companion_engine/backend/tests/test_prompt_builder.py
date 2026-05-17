"""Prompt Builder tests for the compressed local-model expression prompt."""

from app.llm.prompt_builder import build_prompt
from app.schemas.emotion import ConversationIntent, EmotionType, RiskLevel
from app.schemas.engine import DialogueContext, SceneContext
from app.schemas.long_term_memory import LongTermMemory
from app.schemas.memory import UserProfile
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState
from app.schemas.strategy import EmpathyStrategy


def test_prompt_is_short_expression_task_not_full_state_dump() -> None:
    """The local model should only receive a compressed reply-writing task."""
    context = DialogueContext(
        user_id="user_a",
        event_type="user_direct_chat",
        user_text="我今天有点累",
        scene=SceneContext(time="21:00", location="卧室", is_user_nearby=True),
    )
    memory = LongTermMemory(
        memory_type="preference",
        content="用户喜欢安静陪伴",
        importance=0.8,
        source_text="我累的时候别问太多。",
    )

    prompt = build_prompt(
        user_text="我今天有点累",
        context=context,
        user_profile=UserProfile(
            user_id="user_a",
            preferred_support_style="listen_first",
            disliked_responses=["过早分析"],
        ),
        persona=PersonaSnapshot(warmth_level="medium"),
        relationship_state=RelationshipState(user_id="user_a", relationship_stage="familiar"),
        memories=[memory],
        intent=ConversationIntent.casual_chat,
        emotion=EmotionType.tired,
        risk_level=RiskLevel.none,
        strategy=EmpathyStrategy.quiet_company,
    )

    assert "<|im_start|>system" in prompt
    assert "<|im_start|>user" in prompt
    assert "用户刚刚说：我今天有点累" in prompt
    assert "用户偏好的支持方式：listen_first" in prompt
    assert "避免这些回复方式：过早分析" in prompt
    assert "关系分寸：有点熟悉" in prompt
    assert "可轻轻参考这条记忆：用户喜欢安静陪伴" in prompt
    assert "回复方向：轻轻陪伴，不追问。" in prompt
    assert "只输出一句自然中文回复" in prompt
    assert "不要 JSON" in prompt
    assert '"reply_text"' not in prompt
    assert "model_dump" not in prompt
    assert "trust_level" not in prompt
