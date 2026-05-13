"""用户状态模型。

定义用户活动和状态追踪。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class UserActivityLevel(str, Enum):
    """用户活跃度"""
    VERY_HIGH = "very_high"    # 非常活跃 (>10次/天)
    HIGH = "high"              # 活跃 (5-10次/天)
    NORMAL = "normal"         # 正常 (2-5次/天)
    LOW = "low"               # 低活跃 (1-2次/天)
    VERY_LOW = "very_low"     # 很低 (<1次/天)
    INACTIVE = "inactive"     # 不活跃 (>24h无互动)


@dataclass
class UserActivity:
    """用户活动记录"""
    timestamp: datetime
    action_type: str  # "message", "proactive", "reminder"
    content_preview: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "content_preview": self.content_preview[:100] if self.content_preview else "",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserActivity":
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            timestamp=ts or datetime.now(),
            action_type=data.get("action_type", "message"),
            content_preview=data.get("content_preview", ""),
        )


@dataclass
class UserState:
    """用户状态"""
    user_id: str = "default"
    last_activity: Optional[datetime] = None
    last_proactive_message: Optional[datetime] = None
    last_session_end: Optional[datetime] = None
    message_count_today: int = 0
    daily_message_counts: Dict[str, int] = field(default_factory=dict)  # date -> count
    activity_history: List[UserActivity] = field(default_factory=list)

    # 用户主动说话相关
    user_spoke_first: bool = False  # 用户是否主动说话
    user_initiated_count: int = 0   # 用户主动发起的次数
    consecutive_proactive_count: int = 0  # 连续主动提问次数
    user_response_count: int = 0     # 用户响应次数

    # 用户偏好
    preferred_topics: List[str] = field(default_factory=list)
    conversation_style: str = "friendly"  # friendly, formal, casual

    def __post_init__(self):
        """初始化后处理"""
        if not self.last_activity:
            self.last_activity = datetime.now()

    def record_user_activity(self, action_type: str = "message", content: str = "") -> None:
        """记录用户活动"""
        self.last_activity = datetime.now()

        # 记录活动
        activity = UserActivity(
            timestamp=datetime.now(),
            action_type=action_type,
            content_preview=content[:100] if content else "",
        )
        self.activity_history.append(activity)

        # 保持最近100条记录
        if len(self.activity_history) > 100:
            self.activity_history = self.activity_history[-100:]

        # 更新今日消息数
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_message_counts[today] = self.daily_message_counts.get(today, 0) + 1
        self.message_count_today = self.daily_message_counts[today]

    def record_user_spoke_first(self) -> None:
        """记录用户主动说话"""
        self.user_spoke_first = True
        self.user_initiated_count += 1
        self.consecutive_proactive_count = 0  # 重置连续主动计数
        self.user_response_count += 1
        self.record_user_activity("user_initiated")

    def record_proactive_message(self) -> None:
        """记录系统主动消息"""
        self.last_proactive_message = datetime.now()
        self.consecutive_proactive_count += 1
        self.record_user_activity("proactive")

    def record_session_end(self) -> None:
        """记录会话结束"""
        self.last_session_end = datetime.now()

    def get_activity_level(self) -> UserActivityLevel:
        """获取活跃度等级"""
        if not self.last_activity:
            return UserActivityLevel.INACTIVE

        hours_since_activity = (datetime.now() - self.last_activity).total_seconds() / 3600

        # 超过24小时不活跃
        if hours_since_activity > 24:
            return UserActivityLevel.INACTIVE

        # 基于今日消息数判断
        if self.message_count_today > 10:
            return UserActivityLevel.VERY_HIGH
        elif self.message_count_today > 5:
            return UserActivityLevel.HIGH
        elif self.message_count_today >= 2:
            return UserActivityLevel.NORMAL
        elif self.message_count_today >= 1:
            return UserActivityLevel.LOW
        else:
            return UserActivityLevel.VERY_LOW

    def get_idle_hours(self) -> float:
        """获取空闲小时数"""
        if not self.last_activity:
            return 0
        return (datetime.now() - self.last_activity).total_seconds() / 3600

    def should_adjust_proactive_strategy(self) -> bool:
        """是否需要调整主动策略"""
        # 如果用户连续5次以上主动说话，减少主动
        if self.consecutive_proactive_count >= 5:
            return True

        # 如果用户活跃度高，减少打扰
        level = self.get_activity_level()
        if level in (UserActivityLevel.VERY_HIGH, UserActivityLevel.HIGH):
            return True

        return False

    def get_recommended_interval(self, base_interval: int) -> int:
        """获取推荐检查间隔"""
        level = self.get_activity_level()

        multipliers = {
            UserActivityLevel.VERY_HIGH: 3.0,
            UserActivityLevel.HIGH: 2.0,
            UserActivityLevel.NORMAL: 1.0,
            UserActivityLevel.LOW: 0.5,
            UserActivityLevel.VERY_LOW: 0.3,
            UserActivityLevel.INACTIVE: 0.2,
        }

        multiplier = multipliers.get(level, 1.0)
        recommended = int(base_interval * multiplier)

        # 限制范围
        return max(10, min(recommended, 300))  # 10秒到5分钟

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "last_proactive_message": self.last_proactive_message.isoformat() if self.last_proactive_message else None,
            "last_session_end": self.last_session_end.isoformat() if self.last_session_end else None,
            "message_count_today": self.message_count_today,
            "daily_message_counts": self.daily_message_counts,
            "activity_history": [a.to_dict() for a in self.activity_history[-20:]],
            "user_spoke_first": self.user_spoke_first,
            "user_initiated_count": self.user_initiated_count,
            "consecutive_proactive_count": self.consecutive_proactive_count,
            "user_response_count": self.user_response_count,
            "preferred_topics": self.preferred_topics,
            "conversation_style": self.conversation_style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserState":
        """从字典创建"""
        state = cls()

        state.user_id = data.get("user_id", "default")

        last_activity = data.get("last_activity")
        if last_activity:
            state.last_activity = datetime.fromisoformat(last_activity)

        last_proactive = data.get("last_proactive_message")
        if last_proactive:
            state.last_proactive_message = datetime.fromisoformat(last_proactive)

        last_session = data.get("last_session_end")
        if last_session:
            state.last_session_end = datetime.fromisoformat(last_session)

        state.message_count_today = data.get("message_count_today", 0)
        state.daily_message_counts = data.get("daily_message_counts", {})
        state.user_spoke_first = data.get("user_spoke_first", False)
        state.user_initiated_count = data.get("user_initiated_count", 0)
        state.consecutive_proactive_count = data.get("consecutive_proactive_count", 0)
        state.user_response_count = data.get("user_response_count", 0)
        state.preferred_topics = data.get("preferred_topics", [])
        state.conversation_style = data.get("conversation_style", "friendly")

        history = data.get("activity_history", [])
        state.activity_history = [UserActivity.from_dict(a) for a in history]

        return state
