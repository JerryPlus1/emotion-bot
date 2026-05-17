"""节奏控制文件，负责根据关系阶段控制说话分寸。"""

from app.schemas.relationship import RelationshipState


def get_allowed_intimacy_level(state: RelationshipState) -> str:
    """根据关系阶段返回允许表达的亲密度等级。"""
    stage_to_level = {
        "stranger": "low",
        "familiar": "medium",
        "trusted": "medium_high",
        "close_friend": "high",
    }

    # 未知阶段保守处理，默认只允许低亲密度表达。
    return stage_to_level.get(state.relationship_stage, "low")


def should_avoid_deep_question(state: RelationshipState) -> bool:
    """判断当前是否应该避免深入私人问题。"""
    if state.relationship_stage == "stranger":
        return True

    if state.relationship_stage == "familiar" and state.user_openness < 0.4:
        return True

    return False
