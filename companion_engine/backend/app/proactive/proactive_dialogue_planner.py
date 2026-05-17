"""主动对话规划文件，负责选择主动互动类型。"""

from typing import Any


def choose_proactive_type(
    context: Any,
    user_profile: Any,
    relationship_state: Any,
    question_type: str,
) -> str:
    """根据问题类型、用户画像和关系阶段选择主动互动类型。"""
    # 当前阶段不使用 context，但保留参数给后续结合场景事件扩展。
    _ = context

    if question_type == "profile_question":
        return "profile_question"

    if question_type == "persona_question":
        return "persona_question"

    if user_profile.initiative_tolerance == "low":
        return "quiet_company"

    if relationship_state.relationship_stage == "stranger":
        return "soft_greeting"

    if relationship_state.relationship_stage in ["trusted", "close_friend"]:
        return "memory_recall"

    return "quiet_company"
