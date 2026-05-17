"""回复评估文件，用规则粗略判断用户对上一轮回复的反应。"""

STRONG_POSITIVE_KEYWORDS = ("你懂我", "谢谢", "好温暖", "继续说", "你真好")
NEUTRAL_KEYWORDS = ("嗯", "哦", "好吧", "行吧")
NEGATIVE_KEYWORDS = ("别问", "烦", "闭嘴", "不想聊", "你很烦")


def evaluate_user_reaction(user_text: str | None) -> tuple[str, float]:
    """根据用户新消息粗略评估反馈类型和质量分。"""
    if not user_text:
        return "neutral", 0.4

    if any(keyword in user_text for keyword in STRONG_POSITIVE_KEYWORDS):
        return "strong_positive", 0.9

    if any(keyword in user_text for keyword in NEUTRAL_KEYWORDS):
        return "neutral", 0.5

    if any(keyword in user_text for keyword in NEGATIVE_KEYWORDS):
        return "negative", 0.2

    if len(user_text) > 20:
        return "positive", 0.75

    return "neutral", 0.5
