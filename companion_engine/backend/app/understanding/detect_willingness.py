"""意愿识别文件，用简单关键词规则判断用户是否愿意继续互动。"""

WILLING_KEYWORDS = ("继续", "想说", "陪我聊", "你说")
UNWILLING_KEYWORDS = ("别问", "不想说", "安静", "算了")


def detect_willingness(text: str | None) -> str:
    """识别用户继续聊天意愿，返回 willing、neutral 或 unwilling。"""
    if not text:
        return "neutral"

    # 先识别不愿意互动，避免“别问了你说吧”之类文本被误判为愿意。
    if any(keyword in text for keyword in UNWILLING_KEYWORDS):
        return "unwilling"

    if any(keyword in text for keyword in WILLING_KEYWORDS):
        return "willing"

    return "neutral"
