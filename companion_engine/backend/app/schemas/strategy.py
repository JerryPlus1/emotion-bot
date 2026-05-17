"""策略 Schema 文件，定义陪伴回复策略枚举。"""

from enum import Enum


class EmpathyStrategy(str, Enum):
    """共情策略，用于指导机器人选择本轮回复方式。"""

    quiet_company = "quiet_company"
    emotional_validation = "emotional_validation"
    choice_offering = "choice_offering"
    soft_greeting = "soft_greeting"
    profile_question = "profile_question"
    persona_question = "persona_question"
    playful_response = "playful_response"
    crisis_redirect = "crisis_redirect"
    memory_recall = "memory_recall"
