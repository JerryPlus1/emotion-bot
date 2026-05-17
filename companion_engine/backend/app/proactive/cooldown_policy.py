"""冷却策略文件，负责限制机器人主动开口频率。"""

from app.proactive.proactive_store import count_recent_proactive


def is_in_cooldown(user_id: str, db_path: str) -> bool:
    """最近 60 分钟主动开口达到 2 次时进入冷却。"""
    return count_recent_proactive(user_id=user_id, minutes=60, db_path=db_path) >= 2
