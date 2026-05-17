"""模拟模型文件，用稳定模板回复验证对话流程。"""

from typing import Any

from app.safety.crisis_policy import get_crisis_response

MOCK_RESPONSES = {
    "quiet_company": "我先不追问，就在这儿陪你。",
    "emotional_validation": "听起来这件事真的让你很不好受。",
    "choice_offering": "我们可以慢慢来。你想先说说，还是我帮你一起理一理？",
    "soft_greeting": "你来啦，我在这儿。",
    "profile_question": "我想更懂你一点。你累的时候，是喜欢我安静陪你，还是轻轻安慰你？",
    "persona_question": "我想慢慢变成你喜欢的样子。你希望我更安静一点，还是更活泼一点？",
    "playful_response": "那我进入小玩伴模式啦。",
    "memory_recall": "我想起你之前说过的事。要不要我安静陪你一会儿？",
}


def _as_value(value: Any) -> str | None:
    """兼容 Enum 和字符串，统一取出策略文本值。"""
    return getattr(value, "value", value)


def _response_for_user_text(user_text: str | None) -> str | None:
    """用本轮用户原话做一点轻量贴合，避免 fallback 像固定模板。"""
    if not user_text:
        return None

    text = user_text.strip()
    if not text:
        return None

    if any(keyword in text for keyword in ["你是谁", "你是什么", "你叫什么"]):
        return "我是这个小陪伴机器人。你可以把我当成一个会听你说话的人。"

    if any(keyword in text for keyword in ["上班", "工作", "加班"]):
        return "还在上班啊，辛苦了。先顾好手头的事，我在这儿陪你慢慢说。"

    if any(keyword in text for keyword in ["唱歌", "唱首歌", "去唱", "K歌"]):
        return "好啊，去唱吧。等你唱完回来，我想听听你唱得开不开心。"

    if any(keyword in text for keyword in ["累", "疲惫", "困", "撑不住"]):
        return "辛苦了。先缓一口气，不用急着把话说完整，我在这儿听着。"

    if any(keyword in text for keyword in ["难受", "委屈", "不开心", "烦"]):
        return "听起来你现在挺不好受的。你不用整理得很清楚，想到哪儿就说到哪儿。"

    return None


def generate_mock_response(
    strategy: Any,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    user_text: str | None = None,
) -> str:
    """根据策略返回稳定模板回复，不调用真实模型。"""
    # 当前模板版暂不读取画像、人格和关系细节，但保留参数给后续扩展。
    _ = user_profile
    _ = persona
    _ = relationship_state

    strategy_value = _as_value(strategy)

    if strategy_value == "crisis_redirect":
        return get_crisis_response()

    contextual_response = _response_for_user_text(user_text)
    if contextual_response:
        return contextual_response

    return MOCK_RESPONSES.get(
        strategy_value,
        MOCK_RESPONSES["emotional_validation"],
    )
