"""情绪 Schema 文件，定义情绪、风险和会话意图枚举。"""

from enum import Enum


class EmotionType(str, Enum):
    """用户情绪类型，用于描述当前对话中的主要情绪。"""

    neutral = "neutral"
    tired = "tired"
    sad = "sad"
    angry = "angry"
    anxious = "anxious"
    happy = "happy"


class RiskLevel(str, Enum):
    """风险等级，用于描述当前对话的安全风险程度。"""

    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


class ConversationIntent(str, Enum):
    """会话意图，用于描述用户当前最可能的互动目的。"""

    casual_chat = "casual_chat"
    seeking_comfort = "seeking_comfort"
    seeking_advice = "seeking_advice"
    wants_space = "wants_space"
    playful = "playful"
    explicit_feedback = "explicit_feedback"
