"""关系化称呼策略，根据画像和关系阶段决定是否自然加入称呼。"""

from typing import Any

BLOCKED_ADDRESSES = {"主人", "我的主人", "宝贝主人"}


def _stage(relationship_state: Any) -> str:
    """读取关系阶段，缺失时保守按 stranger 处理。"""
    return getattr(relationship_state, "relationship_stage", "stranger")


def _preferred_address(user_profile: Any) -> str | None:
    """读取用户偏好称呼，并过滤不合适称呼。"""
    address = getattr(user_profile, "preferred_address", None)
    if not address:
        return None

    normalized = str(address).strip()
    if not normalized or normalized in BLOCKED_ADDRESSES:
        return None

    return normalized


def choose_address(user_profile: Any, relationship_state: Any) -> str | None:
    """选择本轮可使用的称呼。"""
    stage = _stage(relationship_state)
    address = _preferred_address(user_profile)

    if stage == "stranger":
        return None

    if stage == "familiar":
        return "你"

    if stage in ["trusted", "close_friend"]:
        return address

    return None


def apply_addressing(text: str, user_profile: Any, relationship_state: Any) -> str:
    """在回复中自然加入一次称呼，避免每句话都叫人。"""
    stage = _stage(relationship_state)
    address = choose_address(user_profile, relationship_state)
    cleaned = text.strip()

    if not cleaned or address is None:
        return cleaned

    if stage == "stranger":
        return cleaned

    # 文本太短时不强行加称呼，避免显得用力。
    if len(cleaned) <= 12:
        return cleaned

    # 已经出现称呼时不重复添加。
    if address in cleaned:
        return cleaned

    # familiar 阶段“你”本来就常见，不额外硬加。
    if stage == "familiar":
        return cleaned

    if stage == "close_friend":
        return f"{address}，{cleaned}"

    return cleaned
