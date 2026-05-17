"""关系状态测试，验证关系存储、更新和节奏控制规则。"""

from pathlib import Path

from app.db.init_db import init_db
from app.relationship.pacing_controller import (
    get_allowed_intimacy_level,
    should_avoid_deep_question,
)
from app.relationship.relationship_store import (
    get_relationship_state,
    save_relationship_state,
)
from app.relationship.relationship_updater import update_relationship_after_interaction
from app.schemas.relationship import RelationshipState


def _temp_db(tmp_path: Path) -> str:
    """创建临时数据库并返回路径，避免污染真实 data 目录。"""
    db_path = tmp_path / "companion.db"
    init_db(str(db_path))
    return str(db_path)


def test_default_relationship_state_is_correct(tmp_path: Path) -> None:
    """测试首次读取关系状态时返回默认值。"""
    db_path = _temp_db(tmp_path)

    state = get_relationship_state("user_a", db_path)

    assert state == RelationshipState(user_id="user_a")


def test_save_relationship_state_can_be_read_back(tmp_path: Path) -> None:
    """测试保存后的关系状态可以读回。"""
    db_path = _temp_db(tmp_path)
    state = RelationshipState(
        user_id="user_a",
        relationship_stage="familiar",
        trust_level=0.45,
        intimacy_level=0.2,
        user_openness=0.5,
        recent_interaction_quality="positive",
        last_meaningful_topic="音乐",
    )

    save_relationship_state(state, db_path)
    saved_state = get_relationship_state("user_a", db_path)

    assert saved_state == state


def test_positive_feedback_increases_trust_level() -> None:
    """测试正反馈会提高信任度。"""
    state = RelationshipState(user_id="user_a")

    updated = update_relationship_after_interaction(state, "positive")

    assert updated.trust_level == 0.25
    assert updated.recent_interaction_quality == "positive"


def test_strong_positive_feedback_increases_intimacy_level() -> None:
    """测试强正反馈会提高亲密度。"""
    state = RelationshipState(user_id="user_a")

    updated = update_relationship_after_interaction(state, "strong_positive")

    assert updated.intimacy_level == 0.18
    assert updated.recent_interaction_quality == "strong_positive"


def test_negative_feedback_decreases_user_openness() -> None:
    """测试负反馈会降低用户开放度。"""
    state = RelationshipState(user_id="user_a")

    updated = update_relationship_after_interaction(state, "negative")

    assert updated.user_openness == 0.12
    assert updated.recent_interaction_quality == "negative"


def test_scores_are_clamped_between_zero_and_one() -> None:
    """测试关系分数不会超过 1 或低于 0。"""
    high_state = RelationshipState(
        user_id="user_a",
        trust_level=0.98,
        intimacy_level=0.96,
        user_openness=0.98,
    )
    low_state = RelationshipState(
        user_id="user_b",
        trust_level=0.02,
        intimacy_level=0.1,
        user_openness=0.01,
    )

    high_updated = update_relationship_after_interaction(high_state, "strong_positive")
    low_updated = update_relationship_after_interaction(low_state, "negative")

    assert high_updated.trust_level == 1.0
    assert high_updated.intimacy_level == 1.0
    assert high_updated.user_openness == 1.0
    assert low_updated.trust_level == 0.0
    assert low_updated.user_openness == 0.0


def test_relationship_stage_can_progress() -> None:
    """测试关系阶段可以根据分数进入 familiar、trusted 和 close_friend。"""
    familiar = update_relationship_after_interaction(
        RelationshipState(user_id="user_a", trust_level=0.35, intimacy_level=0.1),
        "positive",
    )
    trusted = update_relationship_after_interaction(
        RelationshipState(user_id="user_a", trust_level=0.65, intimacy_level=0.5),
        "positive",
    )
    close_friend = update_relationship_after_interaction(
        RelationshipState(user_id="user_a", trust_level=0.8, intimacy_level=0.75),
        "positive",
    )

    assert familiar.relationship_stage == "familiar"
    assert trusted.relationship_stage == "trusted"
    assert close_friend.relationship_stage == "close_friend"


def test_pacing_controller_returns_expected_intimacy_levels() -> None:
    """测试不同关系阶段对应正确亲密度等级。"""
    assert get_allowed_intimacy_level(
        RelationshipState(user_id="user_a", relationship_stage="stranger")
    ) == "low"
    assert get_allowed_intimacy_level(
        RelationshipState(user_id="user_a", relationship_stage="familiar")
    ) == "medium"
    assert get_allowed_intimacy_level(
        RelationshipState(user_id="user_a", relationship_stage="trusted")
    ) == "medium_high"
    assert get_allowed_intimacy_level(
        RelationshipState(user_id="user_a", relationship_stage="close_friend")
    ) == "high"


def test_should_avoid_deep_question_rules() -> None:
    """测试深入问题规避规则。"""
    assert should_avoid_deep_question(
        RelationshipState(user_id="user_a", relationship_stage="stranger")
    )
    assert should_avoid_deep_question(
        RelationshipState(
            user_id="user_a",
            relationship_stage="familiar",
            user_openness=0.3,
        )
    )
    assert not should_avoid_deep_question(
        RelationshipState(
            user_id="user_a",
            relationship_stage="trusted",
            user_openness=0.3,
        )
    )
