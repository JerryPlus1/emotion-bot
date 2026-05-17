"""沉默陪伴策略，判断什么时候少说一点反而更合适。"""

from typing import Any


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def should_use_silence(
    intent: Any,
    emotion: Any,
    risk_level: Any,
    relationship_state: Any,
    user_profile: Any,
) -> bool:
    """判断当前是否应该使用沉默陪伴回复。"""
    intent_value = _as_value(intent)
    emotion_value = _as_value(emotion)
    risk_value = _as_value(risk_level)

    if risk_value in ["high", "medium"]:
        return False

    if intent_value == "wants_space":
        return True

    if (
        emotion_value == "tired"
        and getattr(user_profile, "preferred_support_style", "unknown") == "quiet_company"
    ):
        return True

    if (
        getattr(relationship_state, "relationship_stage", "stranger")
        in ["trusted", "close_friend"]
        and getattr(relationship_state, "recent_interaction_quality", "neutral") == "negative"
    ):
        return True

    return False


def build_silence_reply(relationship_state: Any) -> str:
    """根据关系阶段生成有分寸的沉默陪伴回复。"""
    stage = getattr(relationship_state, "relationship_stage", "stranger")
    replies = {
        "stranger": "好，我不多问。你想说的时候我在。",
        "familiar": "嗯，我先不问了。就在这儿陪你一会儿。",
        "trusted": "好，我懂。今天就不追着你说了，我在。",
        "close_friend": "嗯，不问了。你靠一会儿就好，我在呢。",
    }
    return replies.get(stage, replies["stranger"])
