"""问题规划文件，负责选择是否提出轻量偏好问题。"""

from typing import Any

NEGATIVE_EMOTIONS = {"sad", "tired", "angry", "anxious"}


def _as_value(value: Any) -> str:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def choose_question_type(
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    intent: Any,
    emotion: Any,
) -> str:
    """根据画像、人格、关系、意图和情绪选择问题类型。"""
    intent_value = _as_value(intent)
    emotion_value = _as_value(emotion)

    # 用户情绪差时先陪伴，不追问偏好问题。
    if emotion_value in NEGATIVE_EMOTIONS:
        return "none"

    # 用户明确想要空间时不提问。
    if intent_value == "wants_space":
        return "none"

    if (
        relationship_state.relationship_stage == "stranger"
        and user_profile.preferred_support_style == "unknown"
    ):
        return "profile_question"

    if user_profile.preferred_support_style == "unknown":
        return "profile_question"

    if (
        relationship_state.relationship_stage != "stranger"
        and persona.warmth_level == "medium"
    ):
        return "persona_question"

    if (
        relationship_state.relationship_stage in ["trusted", "close_friend"]
        and persona.initiative_level == "medium"
    ):
        return "persona_question"

    return "none"
