"""自然停顿重写器，让低落场景的回复有一点呼吸感。"""

import re
from typing import Any

LOW_EMOTIONS = {"sad", "tired", "anxious"}


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _limit_ellipsis(text: str) -> str:
    """限制省略号数量，避免过度戏剧化。"""
    return re.sub(r"…{3,}", "……", text)


def add_natural_pauses(text: str, persona: Any, emotion: Any, strategy: Any) -> str:
    """在适合的情绪场景里加入轻微自然停顿。"""
    _ = persona
    emotion_value = _as_value(emotion)
    strategy_value = _as_value(strategy)
    paused = text.strip()

    if strategy_value == "playful_response":
        return _limit_ellipsis(paused)

    if strategy_value == "quiet_company":
        if "？" in paused or "?" in paused:
            paused = re.sub(r"[^。！？!?]*[？?]", "", paused).strip()
        return _limit_ellipsis(paused)

    if emotion_value in LOW_EMOTIONS and not paused.startswith(("嗯", "先慢一点", "我在")):
        paused = f"嗯……{paused}"

    return _limit_ellipsis(paused)
