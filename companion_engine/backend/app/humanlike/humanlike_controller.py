"""真人感主控制器，串联沉默、提问、记忆、分寸和风格策略。"""

import re
from typing import Any

from app.humanlike.anti_customer_service_filter import remove_customer_service_tone
from app.humanlike.addressing_policy import apply_addressing
from app.humanlike.intimacy_language_policy import adjust_intimacy_language
from app.humanlike.memory_recall_policy import (
    rewrite_memory_reference,
    should_recall_memory,
)
from app.humanlike.natural_pause_rewriter import add_natural_pauses
from app.humanlike.personality_flavor import apply_personality_flavor
from app.humanlike.question_throttle import remove_extra_questions, should_ask_question
from app.humanlike.repetition_guard import avoid_repetitive_reply
from app.humanlike.silence_policy import build_silence_reply, should_use_silence


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _memory_content(memory: Any) -> str:
    """兼容对象和字典读取记忆内容。"""
    if isinstance(memory, dict):
        return str(memory.get("content", ""))
    return str(getattr(memory, "content", ""))


def _cleanup_text(text: str) -> str:
    """清理多余空白和重复标点。"""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"。{2,}", "。", cleaned)
    cleaned = re.sub(r"！{2,}", "！", cleaned)
    cleaned = re.sub(r"？{2,}", "？", cleaned)
    cleaned = re.sub(r"\?{2,}", "?", cleaned)
    return cleaned


def make_reply_humanlike(
    raw_reply: str,
    intent: Any,
    emotion: Any,
    risk_level: Any,
    strategy: Any,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    memories: list[Any],
    recent_bot_messages: list[str],
    emotion_trend: Any = "stable",
) -> str:
    """把模型原始回复改写成更自然、有分寸的最终回复。"""
    if _as_value(risk_level) in ["high", "medium"]:
        return raw_reply

    trend_value = _as_value(emotion_trend)

    if should_use_silence(intent, emotion, risk_level, relationship_state, user_profile):
        return build_silence_reply(relationship_state)

    reply = remove_customer_service_tone(raw_reply)
    effective_emotion = emotion
    if trend_value == "prolonged_low":
        effective_emotion = "sad"
    elif trend_value == "improving" and _as_value(emotion) == "neutral":
        reply = reply.replace("我在这儿。", "感觉好像松了一点。")

    allow_question = should_ask_question(
        recent_bot_messages=recent_bot_messages,
        intent=intent,
        emotion=effective_emotion,
        relationship_state=relationship_state,
        strategy=strategy,
    )
    reply = remove_extra_questions(reply, allow_one=allow_question)

    if should_recall_memory(memories, intent, emotion, relationship_state, strategy):
        content = _memory_content(memories[0])
        if content:
            memory_reference = rewrite_memory_reference(content, relationship_state)
            reply = f"{memory_reference} {reply}"

    reply = adjust_intimacy_language(reply, relationship_state)
    if trend_value == "worsening" and "安全" not in reply:
        reply = f"{reply} 如果这会儿已经有点撑不住，先把安全放前面。"

    reply = add_natural_pauses(reply, persona, effective_emotion, strategy)
    reply = apply_personality_flavor(reply, persona, relationship_state)
    reply = adjust_intimacy_language(reply, relationship_state)
    reply = avoid_repetitive_reply(reply, recent_bot_messages)
    reply = apply_addressing(reply, user_profile, relationship_state)

    return _cleanup_text(reply) or "我在。"
