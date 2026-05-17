"""意图识别文件，用简单关键词规则判断用户当前对话意图。"""

from app.schemas.emotion import ConversationIntent

INTENT_KEYWORDS: list[tuple[ConversationIntent, tuple[str, ...]]] = [
    (ConversationIntent.wants_space, ("不想说", "别问", "算了", "安静", "别管我")),
    (ConversationIntent.seeking_advice, ("怎么办", "帮我想", "给我建议", "我该怎么做")),
    (ConversationIntent.seeking_comfort, ("我好难受", "陪陪我", "安慰我", "抱抱")),
    (ConversationIntent.playful, ("哈哈", "好玩", "逗我", "开个玩笑")),
    (ConversationIntent.explicit_feedback, ("你能不能", "你以后", "我希望你", "你说话能不能")),
]


def detect_intent(text: str | None) -> ConversationIntent:
    """根据关键词识别会话意图；没有命中时返回 casual_chat。"""
    if not text:
        return ConversationIntent.casual_chat

    # 按规则顺序匹配，先处理边界和空间需求，再处理建议、安慰和反馈。
    for intent, keywords in INTENT_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return intent

    return ConversationIntent.casual_chat
