"""关系化称呼测试，验证称呼选择和自然插入规则。"""

from app.humanlike.addressing_policy import apply_addressing, choose_address
from app.schemas.memory import UserProfile
from app.schemas.relationship import RelationshipState


def _profile(address: str | None = None) -> UserProfile:
    """创建测试用用户画像。"""
    return UserProfile(user_id="user_a", preferred_address=address)


def _relationship(stage: str) -> RelationshipState:
    """创建测试用关系状态。"""
    return RelationshipState(user_id="user_a", relationship_stage=stage)


def test_stranger_does_not_use_intimate_address() -> None:
    """测试 stranger 阶段不加亲昵称呼。"""
    state = _relationship("stranger")

    assert choose_address(_profile("小夏"), state) is None
    assert apply_addressing("我先陪你一会儿。", _profile("小夏"), state) == "我先陪你一会儿。"


def test_close_friend_can_use_preferred_address() -> None:
    """测试 close_friend 且有偏好称呼时可以自然使用。"""
    reply = apply_addressing(
        "我先陪你一会儿，今天不用急。",
        _profile("小夏"),
        _relationship("close_friend"),
    )

    assert reply.startswith("小夏，")


def test_address_is_not_repeated_every_sentence() -> None:
    """测试不会每句话重复称呼。"""
    reply = apply_addressing(
        "我先陪你一会儿。今天不用急。慢慢来。",
        _profile("小夏"),
        _relationship("close_friend"),
    )

    assert reply.count("小夏") == 1


def test_blocked_address_is_not_used() -> None:
    """测试禁止使用“主人”等不合适称呼。"""
    state = _relationship("close_friend")

    assert choose_address(_profile("主人"), state) is None
    assert "主人" not in apply_addressing("我先陪你一会儿。", _profile("主人"), state)
