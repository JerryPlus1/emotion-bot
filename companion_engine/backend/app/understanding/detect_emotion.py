"""情绪识别文件，用简单关键词规则判断用户当前情绪。"""

from app.schemas.emotion import EmotionType

EMOTION_KEYWORDS: list[tuple[EmotionType, tuple[str, ...]]] = [
    (EmotionType.tired, ("累", "困", "没力气", "疲惫", "撑不住")),
    (EmotionType.sad, ("难过", "想哭", "委屈", "伤心", "失落")),
    (EmotionType.angry, ("烦", "气死", "讨厌", "生气", "火大")),
    (EmotionType.anxious, ("焦虑", "慌", "担心", "害怕", "紧张")),
    (EmotionType.happy, ("开心", "高兴", "期待", "好棒", "舒服")),
]


def detect_emotion(text: str | None) -> EmotionType:
    """根据关键词识别情绪；没有命中时返回 neutral。"""
    if not text:
        return EmotionType.neutral

    # 按规则顺序匹配，先命中的情绪作为本轮主要情绪。
    for emotion_type, keywords in EMOTION_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return emotion_type

    return EmotionType.neutral
