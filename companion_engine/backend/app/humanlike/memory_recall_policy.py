"""记忆自然提起策略，避免机械地引用长期记忆。"""

from typing import Any

LOW_EMOTIONS = {"sad", "tired", "anxious"}


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def should_recall_memory(
    memories: list[Any],
    intent: Any,
    emotion: Any,
    relationship_state: Any,
    strategy: Any,
) -> bool:
    """判断本轮是否适合自然提起一条记忆。"""
    if not memories:
        return False

    if _as_value(intent) == "wants_space":
        return False

    if getattr(relationship_state, "relationship_stage", "stranger") == "stranger":
        return False

    if _as_value(emotion) in LOW_EMOTIONS:
        return True

    if _as_value(strategy) == "memory_recall":
        return True

    return False


def rewrite_memory_reference(memory_content: str, relationship_state: Any) -> str:
    """把记忆内容改写成自然提起的表达。"""
    stage = getattr(relationship_state, "relationship_stage", "stranger")
    if stage == "close_friend":
        return f"我一下子想到你上次那种状态：{memory_content}"
    if stage == "trusted":
        return f"我想到你之前也有过这种时候：{memory_content}"
    if stage == "familiar":
        return f"之前你提过类似的感觉：{memory_content}"
    return memory_content
