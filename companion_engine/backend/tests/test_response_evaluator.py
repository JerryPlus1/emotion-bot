"""用户反应评估测试，验证规则版反馈分类和关系更新集成。"""

from pathlib import Path

from app.core.engine import handle_event
from app.evaluation.response_evaluator import evaluate_user_reaction
from app.relationship.relationship_store import get_relationship_state
from app.schemas.engine import EngineInput, SceneContext


def _db_path(tmp_path: Path) -> str:
    """返回测试用临时数据库路径，避免污染真实 data 目录。"""
    return str(tmp_path / "companion.db")


def test_strong_positive_feedback() -> None:
    """测试强正反馈识别。"""
    assert evaluate_user_reaction("谢谢，你真好") == ("strong_positive", 0.9)


def test_positive_feedback_by_long_text() -> None:
    """测试长文本反馈识别为正反馈。"""
    feedback_type, quality_score = evaluate_user_reaction("我想继续聊聊今天发生的这些事情，还有后面让我很在意的部分")

    assert feedback_type == "positive"
    assert quality_score == 0.75


def test_neutral_feedback() -> None:
    """测试中性反馈识别。"""
    assert evaluate_user_reaction("嗯") == ("neutral", 0.5)


def test_negative_feedback() -> None:
    """测试负反馈识别。"""
    assert evaluate_user_reaction("别问了，你很烦") == ("negative", 0.2)


def test_empty_feedback() -> None:
    """测试空文本反馈识别。"""
    assert evaluate_user_reaction(None) == ("neutral", 0.4)


def test_engine_positive_feedback_increases_trust_level(tmp_path: Path) -> None:
    """测试引擎中正反馈后 trust_level 会增加。"""
    db_path = _db_path(tmp_path)

    handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="我想继续聊聊今天发生的这些事情，还有后面让我很在意的部分",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        db_path,
    )
    state = get_relationship_state("default_user", db_path)

    assert state.trust_level > 0.2
    assert state.recent_interaction_quality == "positive"
