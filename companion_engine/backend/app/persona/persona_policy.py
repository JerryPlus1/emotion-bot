"""人格策略文件，负责判断人格更新是否可以写入稳定 Persona。"""

from app.schemas.persona import PersonaSnapshot, PersonaUpdate


def should_apply_persona_update(update: PersonaUpdate) -> bool:
    """判断一条人格更新是否允许修改稳定 Persona。"""
    valid_dimensions = set(PersonaSnapshot.model_fields)

    # 只允许更新 PersonaSnapshot 已声明的字段，避免写入未知维度。
    if update.dimension not in valid_dimensions:
        return False

    # 明确用户反馈可以用稍低阈值生效，因为它比推断更可靠。
    if update.source_type == "explicit_feedback" and update.confidence >= 0.6:
        return True

    # 普通来源需要较高置信度，避免频繁改变机器人稳定说话风格。
    return update.confidence >= 0.75
