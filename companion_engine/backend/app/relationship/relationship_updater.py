"""关系更新文件，负责根据互动反馈调整关系分数和阶段。"""

from app.schemas.relationship import RelationshipState


def _clamp_score(value: float) -> float:
    """把关系分数限制在 0 到 1 之间。"""
    # 先四舍五入，避免 0.35 + 0.05 变成 0.399999999 影响阶段判断。
    rounded_value = round(value, 10)
    return max(0.0, min(1.0, rounded_value))


def _decide_relationship_stage(trust_level: float, intimacy_level: float) -> str:
    """根据当前信任和亲密度判断关系阶段。"""
    if trust_level >= 0.85 and intimacy_level >= 0.75:
        return "close_friend"

    if trust_level >= 0.7 and intimacy_level >= 0.5:
        return "trusted"

    if trust_level >= 0.4:
        return "familiar"

    return "stranger"


def update_relationship_after_interaction(
    state: RelationshipState,
    feedback_type: str,
) -> RelationshipState:
    """根据一次互动反馈返回更新后的关系状态。"""
    trust_level = state.trust_level
    intimacy_level = state.intimacy_level
    user_openness = state.user_openness
    recent_interaction_quality = state.recent_interaction_quality

    if feedback_type == "positive":
        trust_level += 0.05
        user_openness += 0.05
        recent_interaction_quality = "positive"
    elif feedback_type == "strong_positive":
        trust_level += 0.1
        intimacy_level += 0.08
        user_openness += 0.05
        recent_interaction_quality = "strong_positive"
    elif feedback_type == "negative":
        trust_level -= 0.05
        user_openness -= 0.08
        recent_interaction_quality = "negative"
    elif feedback_type == "neutral":
        recent_interaction_quality = "neutral"

    trust_level = _clamp_score(trust_level)
    intimacy_level = _clamp_score(intimacy_level)
    user_openness = _clamp_score(user_openness)

    return RelationshipState(
        user_id=state.user_id,
        relationship_stage=_decide_relationship_stage(trust_level, intimacy_level),
        trust_level=trust_level,
        intimacy_level=intimacy_level,
        user_openness=user_openness,
        recent_interaction_quality=recent_interaction_quality,
        last_meaningful_topic=state.last_meaningful_topic,
    )
