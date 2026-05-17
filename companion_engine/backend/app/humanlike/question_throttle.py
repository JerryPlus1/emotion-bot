"""提问节流策略，避免机器人连续追问。"""

import re
from typing import Any

LOW_EMOTIONS = {"sad", "tired", "angry", "anxious"}
QUESTION_STRATEGIES = {"profile_question", "persona_question"}


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _split_sentences(text: str) -> list[str]:
    """按常见句末标点拆分句子。"""
    return [part.strip() for part in re.findall(r"[^。！？!?]+[。！？!?]?", text) if part.strip()]


def should_ask_question(
    recent_bot_messages: list[str],
    intent: Any,
    emotion: Any,
    relationship_state: Any,
    strategy: Any,
) -> bool:
    """判断本轮回复是否允许带问题。"""
    intent_value = _as_value(intent)
    emotion_value = _as_value(emotion)
    strategy_value = _as_value(strategy)

    if intent_value == "wants_space":
        return False

    if emotion_value in LOW_EMOTIONS:
        return False

    recent_three = recent_bot_messages[-3:]
    question_message_count = sum(1 for message in recent_three if "？" in message or "?" in message)
    if question_message_count >= 2:
        return False

    # stranger 阶段只允许画像/Persona 这类轻问题，其他追问先收住。
    if getattr(relationship_state, "relationship_stage", "stranger") == "stranger":
        return strategy_value in QUESTION_STRATEGIES

    if strategy_value in QUESTION_STRATEGIES:
        return True

    return False


def remove_extra_questions(text: str, allow_one: bool = True) -> str:
    """删除多余问句；允许时最多保留一个问句。"""
    kept: list[str] = []
    kept_question = False

    for sentence in _split_sentences(text):
        has_question = "？" in sentence or "?" in sentence
        if has_question:
            if not allow_one or kept_question:
                continue
            kept_question = True
        kept.append(sentence)

    return "".join(kept).strip()
