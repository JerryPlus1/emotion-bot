"""上下文构建文件，负责组装引擎本轮对话上下文。"""

from typing import Any

from app.schemas.engine import DialogueContext, EngineInput


def build_context(
    input_data: EngineInput,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    memories: list[Any],
) -> DialogueContext:
    """把输入、场景、用户状态和记忆组合成 DialogueContext。"""
    # 当前 DialogueContext 只保存输入和记忆；画像、人格和关系由引擎继续显式传递。
    _ = user_profile
    _ = persona
    _ = relationship_state

    return DialogueContext(
        user_id=input_data.user_id,
        event_type=input_data.event_type,
        user_text=input_data.user_text,
        scene=input_data.scene,
        recent_memories=[],
        important_memories=memories,
    )
