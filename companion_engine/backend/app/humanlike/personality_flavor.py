"""轻微个性风味，让回复贴近 Persona 但不抢用户情绪。"""

import re
from typing import Any

LOW_EMOTIONS = {"sad", "tired", "angry", "anxious"}
ANALYSIS_MARKERS = ["原因可能是", "从逻辑上看", "我们可以分析", "这说明"]


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _split_sentences(text: str) -> list[str]:
    """按常见句末标点拆分句子。"""
    return [part.strip() for part in re.findall(r"[^。！？!?]+[。！？!?]?", text) if part.strip()]


def _limit_sentences(text: str, count: int) -> str:
    """限制句子数量。"""
    return "".join(_split_sentences(text)[:count]).strip()


def _remove_analysis_sentences(text: str) -> str:
    """删除明显解释和分析句。"""
    return "".join(
        sentence
        for sentence in _split_sentences(text)
        if not any(marker in sentence for marker in ANALYSIS_MARKERS)
    ).strip()


def apply_personality_flavor(text: str, persona: Any, relationship_state: Any) -> str:
    """根据 Persona 增加轻微风格，同时控制长度和分析感。"""
    _ = relationship_state
    flavored = text.strip()

    if getattr(persona, "analysis_level", "medium") == "low":
        flavored = _remove_analysis_sentences(flavored) or flavored

    if getattr(persona, "companionship_style", "listen_first") == "listen_first":
        flavored = flavored.replace("你应该", "先不用急着")

    if getattr(persona, "warmth_level", "medium") == "high" and "我在" not in flavored:
        flavored = f"{flavored} 我在。"

    # playfulness 只在情绪不差时轻轻加一点，不抢用户情绪。
    if (
        getattr(persona, "playfulness_level", "medium") == "high"
        and not any(marker in flavored for marker in LOW_EMOTIONS)
        and "小玩伴" not in flavored
    ):
        flavored = flavored.replace("。", "。我轻轻接住这句。", 1)

    if getattr(persona, "speech_length", "medium") == "short":
        flavored = _limit_sentences(flavored, 2)

    return flavored.strip() or "我在。"
