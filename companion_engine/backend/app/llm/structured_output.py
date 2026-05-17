"""结构化模型输出协议，负责把本地模型文本解析为稳定数据结构。"""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ModelReply(BaseModel):
    """本地模型回复协议，方便前端和硬件层读取结构化信息。"""

    reply_text: str = Field(description="最终给用户看的回复文本。")
    inner_emotion: str = Field(default="calm", description="模型内部表达情绪。")
    suggested_expression: str = Field(default="neutral", description="建议硬件表情。")
    should_ask_followup: bool = Field(default=False, description="是否建议继续追问。")
    memory_reference_used: bool = Field(default=False, description="是否引用了长期记忆。")
    confidence: float = Field(default=0.5, ge=0, le=1, description="模型对回复质量的信心。")


def _safe_float_confidence(value: Any) -> float:
    """把 confidence 容错修正到 0 到 1。"""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5

    return max(0.0, min(1.0, confidence))


def _model_reply_from_dict(data: dict[str, Any], fallback_text: str) -> ModelReply:
    """从字典构造 ModelReply，并为缺失字段填默认值。"""
    normalized = {
        "reply_text": data.get("reply_text") or fallback_text,
        "inner_emotion": data.get("inner_emotion") or "calm",
        "suggested_expression": data.get("suggested_expression") or "neutral",
        "should_ask_followup": bool(data.get("should_ask_followup", False)),
        "memory_reference_used": bool(data.get("memory_reference_used", False)),
        "confidence": _safe_float_confidence(data.get("confidence", 0.5)),
    }

    try:
        return ModelReply(**normalized)
    except ValidationError:
        return ModelReply(reply_text=fallback_text, confidence=0.5)


def _find_json_object(text: str) -> dict[str, Any] | None:
    """Return the first JSON object embedded in model text, if one exists."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue

        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            return parsed

    return None


def parse_model_reply(raw_text: str) -> ModelReply:
    """优先解析 JSON；失败时把原文本作为 reply_text。"""
    stripped = raw_text.strip()
    if not stripped:
        return ModelReply(reply_text="", confidence=0.5)

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = _find_json_object(stripped)
        if parsed is None:
            return ModelReply(reply_text=raw_text, confidence=0.5)

    if not isinstance(parsed, dict):
        return ModelReply(reply_text=raw_text, confidence=0.5)

    return _model_reply_from_dict(parsed, fallback_text=raw_text)
