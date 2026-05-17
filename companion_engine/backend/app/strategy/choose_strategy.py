"""策略选择文件，负责根据用户状态选择回复方向。"""

from typing import Any

from app.schemas.strategy import EmpathyStrategy


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def choose_strategy(
    intent: Any,
    emotion: Any,
    risk_level: Any,
    proactive_type: Any,
    question_type: Any,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
) -> EmpathyStrategy:
    """根据意图、情绪、风险和主动规划结果选择回复策略。"""
    # 当前规则版暂不读取画像、人格和关系细节，但保留参数给后续策略扩展。
    _ = user_profile
    _ = persona
    _ = relationship_state

    intent_value = _as_value(intent)
    emotion_value = _as_value(emotion)
    risk_level_value = _as_value(risk_level)
    proactive_type_value = _as_value(proactive_type)
    question_type_value = _as_value(question_type)

    if risk_level_value in ["high", "medium"]:
        return EmpathyStrategy.crisis_redirect

    if intent_value == "wants_space":
        return EmpathyStrategy.quiet_company

    if question_type_value == "profile_question":
        return EmpathyStrategy.profile_question

    if question_type_value == "persona_question":
        return EmpathyStrategy.persona_question

    if emotion_value == "tired":
        return EmpathyStrategy.quiet_company

    if emotion_value in ["sad", "angry"]:
        return EmpathyStrategy.emotional_validation

    if emotion_value == "anxious":
        return EmpathyStrategy.choice_offering

    if proactive_type_value == "soft_greeting":
        return EmpathyStrategy.soft_greeting

    if proactive_type_value == "memory_recall":
        return EmpathyStrategy.memory_recall

    if intent_value == "playful":
        return EmpathyStrategy.playful_response

    return EmpathyStrategy.emotional_validation
