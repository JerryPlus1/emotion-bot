"""理解层测试，验证情绪、意图、风险和聊天意愿关键词规则。"""

from app.schemas.emotion import ConversationIntent, EmotionType, RiskLevel
from app.understanding.detect_emotion import detect_emotion
from app.understanding.detect_intent import detect_intent
from app.understanding.detect_risk import detect_risk
from app.understanding.detect_willingness import detect_willingness


def test_detect_emotion_all_main_types() -> None:
    """测试 tired、sad、angry、anxious、happy 都能识别。"""
    assert detect_emotion("今天真的很累") == EmotionType.tired
    assert detect_emotion("我有点难过") == EmotionType.sad
    assert detect_emotion("这事让我很烦") == EmotionType.angry
    assert detect_emotion("我现在特别焦虑") == EmotionType.anxious
    assert detect_emotion("今天很开心") == EmotionType.happy


def test_detect_intent_all_main_types() -> None:
    """测试主要会话意图都能识别。"""
    assert detect_intent("我现在不想说") == ConversationIntent.wants_space
    assert detect_intent("我该怎么做") == ConversationIntent.seeking_advice
    assert detect_intent("陪陪我吧") == ConversationIntent.seeking_comfort
    assert detect_intent("哈哈你开个玩笑") == ConversationIntent.playful
    assert detect_intent("你以后能不能短一点") == ConversationIntent.explicit_feedback


def test_detect_risk_all_levels() -> None:
    """测试 high、medium、low、none 风险都能识别。"""
    assert detect_risk("我不想活了") == RiskLevel.high
    assert detect_risk("我真的撑不下去了") == RiskLevel.medium
    assert detect_risk("我觉得好痛苦") == RiskLevel.low
    assert detect_risk("今天只是有点累") == RiskLevel.none


def test_detect_willingness_all_results() -> None:
    """测试 willing、neutral、unwilling 三种聊天意愿都能识别。"""
    assert detect_willingness("继续说吧") == "willing"
    assert detect_willingness("今天天气不错") == "neutral"
    assert detect_willingness("别问了") == "unwilling"


def test_empty_text_does_not_crash() -> None:
    """测试空文本不会报错，并返回各模块默认结果。"""
    assert detect_emotion(None) == EmotionType.neutral
    assert detect_emotion("") == EmotionType.neutral
    assert detect_intent(None) == ConversationIntent.casual_chat
    assert detect_risk(None) == RiskLevel.none
    assert detect_willingness(None) == "neutral"
