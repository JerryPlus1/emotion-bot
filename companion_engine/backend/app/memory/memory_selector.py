"""记忆选择文件，负责为本轮回复挑选少量合适的长期记忆。"""

from typing import Any

SUPPORTIVE_VALENCES = {"supportive", "warm", "neutral"}
LOW_EMOTIONS = {"sad", "tired", "anxious"}


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _get_attr(value: Any, name: str, default: Any = None) -> Any:
    """兼容对象和字典读取字段。"""
    if isinstance(value, dict):
        return value.get(name, default)

    return getattr(value, name, default)


def select_memories_for_reply(
    memories: list[Any],
    emotion: Any,
    intent: Any,
    relationship_state: Any,
    limit: int = 3,
) -> list[Any]:
    """根据意图、情绪和关系阶段选择用于回复的记忆。"""
    intent_value = _as_value(intent)
    emotion_value = _as_value(emotion)
    stage = _get_attr(relationship_state, "relationship_stage", "stranger")

    # 用户想要空间时，不强行引用记忆制造被观察感。
    if intent_value == "wants_space":
        return []

    effective_limit = max(0, limit)
    if stage == "stranger":
        effective_limit = min(effective_limit, 1)

    selected_memories = list(memories)

    # 情绪低落时优先使用支持性、温暖或中性的记忆。
    if emotion_value in LOW_EMOTIONS:
        selected_memories.sort(
            key=lambda memory: (
                _get_attr(memory, "emotional_valence") not in SUPPORTIVE_VALENCES,
                -float(_get_attr(memory, "importance", 0.0) or 0.0),
            )
        )

    return selected_memories[:effective_limit]
