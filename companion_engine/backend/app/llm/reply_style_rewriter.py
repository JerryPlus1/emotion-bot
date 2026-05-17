"""回复风格重写文件，用规则后处理让回复更自然、有分寸。"""

import re
from typing import Any

CUSTOMER_SERVICE_PHRASES = [
    "很高兴为你服务",
    "请问还有什么可以帮您",
    "作为一个AI",
]
ANALYSIS_MARKERS = ["原因可能是", "从逻辑上看", "我们可以分析"]
INTIMATE_WORDS_FOR_STRANGER = ["亲爱的", "宝贝", "乖", "抱抱你"]


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def _split_sentences(text: str) -> list[str]:
    """按中文和英文句末标点粗略切分句子。"""
    parts = re.findall(r"[^。！？!?]+[。！？!?]?", text)
    return [part.strip() for part in parts if part.strip()]


def _remove_customer_service_tone(text: str) -> str:
    """去掉明显客服腔和 AI 自我声明。"""
    cleaned = text
    for phrase in CUSTOMER_SERVICE_PHRASES:
        cleaned = cleaned.replace(phrase, "")
    return cleaned


def _remove_analysis_sentences(text: str) -> str:
    """删除明显分析型句子，适配低分析 Persona。"""
    sentences = _split_sentences(text)
    kept = [
        sentence
        for sentence in sentences
        if not any(marker in sentence for marker in ANALYSIS_MARKERS)
    ]
    return "".join(kept)


def _keep_only_first_question(text: str) -> str:
    """如果问题超过一个，只保留第一个问题，减少连续追问感。"""
    question_count = text.count("？") + text.count("?")
    if question_count <= 1:
        return text

    result: list[str] = []
    seen_question = False

    for sentence in _split_sentences(text):
        has_question = "？" in sentence or "?" in sentence
        if has_question and seen_question:
            continue

        if has_question:
            seen_question = True
        result.append(sentence)

    return "".join(result)


def _limit_sentence_count(text: str, max_sentences: int) -> str:
    """按 Persona 的回复长度偏好限制句子数量。"""
    sentences = _split_sentences(text)
    return "".join(sentences[:max_sentences])


def _soften_stranger_intimacy(text: str) -> str:
    """陌生关系下去掉过亲密称呼，保持分寸感。"""
    softened = text
    for word in INTIMATE_WORDS_FOR_STRANGER:
        softened = softened.replace(word, "")
    return softened


def rewrite_reply_style(
    text: str,
    persona: Any,
    relationship_state: Any,
    strategy: Any,
) -> str:
    """对模型回复做轻量风格重写，减少客服腔、说教和追问。"""
    rewritten = _remove_customer_service_tone(text).strip()
    strategy_value = _as_value(strategy)

    if getattr(persona, "analysis_level", "medium") == "low":
        rewritten = _remove_analysis_sentences(rewritten).strip()

    if getattr(relationship_state, "relationship_stage", "stranger") == "stranger":
        rewritten = _soften_stranger_intimacy(rewritten).strip()

    if strategy_value == "quiet_company":
        # 安静陪伴策略要短，也不要追问。
        rewritten = re.sub(r"[^。！？!?]*[？?]", "", rewritten).strip()
        rewritten = _limit_sentence_count(rewritten, 2).strip()
    else:
        rewritten = _keep_only_first_question(rewritten).strip()
        speech_length = getattr(persona, "speech_length", "medium")
        if speech_length == "short":
            rewritten = _limit_sentence_count(rewritten, 2).strip()
        elif speech_length == "medium":
            rewritten = _limit_sentence_count(rewritten, 4).strip()

    # 如果规则删空了文本，保留一个自然的兜底句，避免空回复。
    return rewritten or "我在这儿。"
