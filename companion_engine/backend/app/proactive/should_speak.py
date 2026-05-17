"""主动发言判断文件，负责判断机器人是否应该主动说话。"""

import re
from datetime import time
from typing import Any

from app.proactive.cooldown_policy import is_in_cooldown

IMPORTANT_EVENTS = {"safety_check", "important_reminder"}
NIGHT_START = time(hour=0, minute=0)
NIGHT_END = time(hour=7, minute=0)


def _parse_scene_time(raw_time: str | None) -> time | None:
    """容错解析场景时间，只识别文本中的 HH:MM 格式。"""
    if not raw_time:
        return None

    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", raw_time)
    if match is None:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))
    return time(hour=hour, minute=minute)


def _is_night_quiet_time(raw_time: str | None) -> bool:
    """判断是否处于 00:00 到 07:00 的夜间安静时段。"""
    parsed_time = _parse_scene_time(raw_time)
    if parsed_time is None:
        return False

    return NIGHT_START <= parsed_time <= NIGHT_END


def should_speak(
    context: Any,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    db_path: str,
) -> tuple[bool, str]:
    """根据上下文、用户画像和冷却策略判断是否主动说话。"""
    # 当前阶段不使用 persona 和 relationship_state，但保留参数给后续策略扩展。
    _ = persona
    _ = relationship_state

    if context.event_type == "user_direct_chat":
        return True, "user_initiated"

    if is_in_cooldown(context.user_id, db_path):
        return False, "cooldown"

    if (
        user_profile.initiative_tolerance == "low"
        and context.event_type not in IMPORTANT_EVENTS
    ):
        return False, "low_initiative_tolerance"

    if _is_night_quiet_time(context.scene.time):
        return False, "night_quiet"

    if not context.scene.is_user_nearby and context.event_type == "ambient_event":
        return False, "user_not_nearby"

    return True, "allowed"
