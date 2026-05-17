"""硬件动作映射文件，负责把回复策略映射为硬件动作。"""

from typing import Any

from app.schemas.hardware import HardwareActions


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出可比较的文本值。"""
    return getattr(value, "value", value)


def map_to_hardware_actions(
    response_text: str | None,
    strategy: Any,
    risk_level: Any,
) -> HardwareActions:
    """根据回复文本、策略和风险等级生成硬件动作。"""
    strategy_value = _as_value(strategy)
    risk_level_value = _as_value(risk_level)

    if risk_level_value == "high":
        return HardwareActions(
            expression="worried",
            light_color="red",
            motion="lean_forward",
            speech_text=response_text,
        )

    if strategy_value == "emotional_validation":
        return HardwareActions(
            expression="warm",
            light_color="soft_white",
            motion="nod",
            speech_text=response_text,
        )

    if strategy_value == "choice_offering":
        return HardwareActions(
            expression="thinking",
            light_color="soft_white",
            motion="idle",
            speech_text=response_text,
        )

    if strategy_value == "quiet_company":
        return HardwareActions(
            expression="neutral",
            light_color="blue",
            motion="idle",
            speech_text=response_text,
        )

    if strategy_value == "crisis_redirect":
        return HardwareActions(
            expression="worried",
            light_color="red",
            motion="lean_forward",
            speech_text=response_text,
        )

    if strategy_value == "playful_response":
        return HardwareActions(
            expression="playful",
            light_color="yellow",
            motion="nod",
            speech_text=response_text,
        )

    return HardwareActions(
        expression="neutral",
        light_color="soft_white",
        motion="idle",
        speech_text=response_text,
    )
