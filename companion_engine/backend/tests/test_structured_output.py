"""结构化模型输出测试。"""

from app.llm.structured_output import parse_model_reply


def test_valid_json_can_be_parsed() -> None:
    """测试合法 JSON 可解析。"""
    reply = parse_model_reply(
        '{"reply_text":"你好","inner_emotion":"warm","suggested_expression":"warm","should_ask_followup":false,"memory_reference_used":true,"confidence":0.8}'
    )

    assert reply.reply_text == "你好"
    assert reply.inner_emotion == "warm"
    assert reply.memory_reference_used is True
    assert reply.confidence == 0.8


def test_non_json_falls_back_to_reply_text() -> None:
    """测试非 JSON 会 fallback 成普通回复文本。"""
    reply = parse_model_reply("我先陪你一会儿。")

    assert reply.reply_text == "我先陪你一会儿。"
    assert reply.confidence == 0.5


def test_embedded_json_can_be_parsed() -> None:
    """测试模型在 JSON 前后夹杂提示词时仍能取出 reply_text。"""
    reply = parse_model_reply(
        '请只输出 JSON 格式内容。\n```json\n{"reply_text":"好啊，去唱吧。","confidence":0.95}\n```\n用户唱歌。'
    )

    assert reply.reply_text == "好啊，去唱吧。"
    assert reply.confidence == 0.95


def test_missing_fields_use_defaults() -> None:
    """测试缺失字段会使用默认值。"""
    reply = parse_model_reply('{"reply_text":"嗯，我在。"}')

    assert reply.reply_text == "嗯，我在。"
    assert reply.inner_emotion == "calm"
    assert reply.suggested_expression == "neutral"
    assert reply.should_ask_followup is False
    assert reply.memory_reference_used is False
    assert reply.confidence == 0.5


def test_confidence_out_of_range_is_clamped() -> None:
    """测试 confidence 超范围会被修正到 0 到 1。"""
    high_reply = parse_model_reply('{"reply_text":"你好","confidence":2}')
    low_reply = parse_model_reply('{"reply_text":"你好","confidence":-1}')

    assert high_reply.confidence == 1.0
    assert low_reply.confidence == 0.0
