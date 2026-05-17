"""重复控制器，减少连续模板化表达和相似回复。"""

from difflib import SequenceMatcher

TEMPLATE_REPLACEMENTS = {
    "我在这儿陪你": "我就在旁边。",
    "听起来真的不太好受": "这一下确实不好扛。",
}


def _similarity(left: str, right: str) -> float:
    """计算两个回复的粗略相似度。"""
    return SequenceMatcher(None, left, right).ratio()


def _count_recent_phrase(phrase: str, recent_bot_messages: list[str]) -> int:
    """统计最近机器人回复中某个短语出现的次数。"""
    return sum(1 for message in recent_bot_messages if phrase in message)


def _shorten_reply(text: str) -> str:
    """无法改写时缩短回复，降低重复感。"""
    for separator in ["。", "！", "？", "!", "?"]:
        if separator in text:
            first = text.split(separator)[0].strip()
            if first:
                return f"{first}{separator}"
    return text[:24].strip() or "我在。"


def avoid_repetitive_reply(
    new_reply: str,
    recent_bot_messages: list[str],
) -> str:
    """根据最近机器人回复改写当前回复，避免重复表达。"""
    adjusted = new_reply.strip()

    for phrase, replacement in TEMPLATE_REPLACEMENTS.items():
        if phrase in adjusted and _count_recent_phrase(phrase, recent_bot_messages) >= 1:
            adjusted = adjusted.replace(phrase, replacement)

    if "慢慢来" in adjusted and _count_recent_phrase("慢慢来", recent_bot_messages) >= 2:
        adjusted = adjusted.replace("慢慢来", "先不用急")

    if any(_similarity(adjusted, message) >= 0.82 for message in recent_bot_messages):
        adjusted = _shorten_reply(adjusted)

    return adjusted or "我在。"
