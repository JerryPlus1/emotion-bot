"""回复风格重写测试，验证客服腔、分析句、追问和亲密称呼控制。"""

from app.llm.reply_style_rewriter import rewrite_reply_style
from app.schemas.persona import PersonaSnapshot
from app.schemas.relationship import RelationshipState
from app.schemas.strategy import EmpathyStrategy


def test_removes_customer_service_tone() -> None:
    """测试能去掉明显客服腔。"""
    text = "很高兴为你服务。我在这儿陪你。请问还有什么可以帮您？"

    rewritten = rewrite_reply_style(
        text,
        PersonaSnapshot(),
        RelationshipState(user_id="user_a", relationship_stage="familiar"),
        EmpathyStrategy.emotional_validation,
    )

    assert "很高兴为你服务" not in rewritten
    assert "请问还有什么可以帮您" not in rewritten


def test_low_analysis_level_removes_analysis_sentences() -> None:
    """测试 analysis_level=low 时减少分析型句子。"""
    text = "原因可能是你太累了。先缓一缓。我在。"

    rewritten = rewrite_reply_style(
        text,
        PersonaSnapshot(analysis_level="low"),
        RelationshipState(user_id="user_a", relationship_stage="familiar"),
        EmpathyStrategy.emotional_validation,
    )

    assert "原因可能是" not in rewritten
    assert "先缓一缓" in rewritten


def test_quiet_company_removes_questions() -> None:
    """测试 quiet_company 策略不追问。"""
    text = "我先陪你。你想说说吗？要不要喝水？"

    rewritten = rewrite_reply_style(
        text,
        PersonaSnapshot(),
        RelationshipState(user_id="user_a", relationship_stage="familiar"),
        EmpathyStrategy.quiet_company,
    )

    assert "？" not in rewritten
    assert "?" not in rewritten


def test_stranger_removes_too_intimate_words() -> None:
    """测试 stranger 阶段不使用太亲密表达。"""
    text = "亲爱的，我在这儿。抱抱你。"

    rewritten = rewrite_reply_style(
        text,
        PersonaSnapshot(),
        RelationshipState(user_id="user_a", relationship_stage="stranger"),
        EmpathyStrategy.emotional_validation,
    )

    assert "亲爱的" not in rewritten
    assert "抱抱你" not in rewritten


def test_medium_length_keeps_at_most_four_sentences() -> None:
    """测试 medium 回复长度最多保留四句。"""
    text = "一句。二句。三句。四句。五句。"

    rewritten = rewrite_reply_style(
        text,
        PersonaSnapshot(speech_length="medium"),
        RelationshipState(user_id="user_a", relationship_stage="trusted"),
        EmpathyStrategy.emotional_validation,
    )

    assert rewritten == "一句。二句。三句。四句。"
