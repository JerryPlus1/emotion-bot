"""用户状态服务。

管理用户活动和状态追踪。
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.user_state import UserState, UserActivityLevel
from logger import debug, info


class UserService:
    """用户服务"""

    _instance: Optional["UserService"] = None
    _state_file = Path(__file__).parent.parent.parent / "user_state.json"

    def __init__(self):
        self.state: UserState = self._load_state()

    @classmethod
    def get_instance(cls) -> "UserService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_state(self) -> UserState:
        """加载用户状态"""
        if self._state_file.exists():
            try:
                with open(self._state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return UserState.from_dict(data)
            except Exception as e:
                debug(f"加载用户状态失败: {e}")
        return UserState()

    def _save_state(self) -> None:
        """保存用户状态"""
        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            debug(f"保存用户状态失败: {e}")

    def record_user_message(self, content: str) -> None:
        """记录用户消息"""
        self.state.record_user_activity("message", content)
        self._save_state()

    def record_user_spoke_first(self) -> None:
        """记录用户主动说话"""
        self.state.record_user_spoke_first()
        self._save_state()
        info(f"用户主动说话，累计: {self.state.user_initiated_count}次")

    def record_proactive_message(self) -> None:
        """记录系统主动消息"""
        self.state.record_proactive_message()
        self._save_state()

    def record_session_end(self) -> None:
        """记录会话结束"""
        self.state.record_session_end()
        self._save_state()

    def get_activity_level(self) -> UserActivityLevel:
        """获取活跃度"""
        return self.state.get_activity_level()

    def get_idle_hours(self) -> float:
        """获取空闲小时数"""
        return self.state.get_idle_hours()

    def should_adjust_strategy(self) -> bool:
        """是否应调整策略"""
        return self.state.should_adjust_proactive_strategy()

    def get_recommended_interval(self, base_interval: int) -> int:
        """获取推荐间隔"""
        return self.state.get_recommended_interval(base_interval)

    def get_user_initiated_ratio(self) -> float:
        """获取用户主动说话比例"""
        total = self.state.user_initiated_count + self.state.consecutive_proactive_count
        if total == 0:
            return 0.5
        return self.state.user_initiated_count / total

    def is_user_mostly_passive(self) -> bool:
        """用户是否主要是被动响应"""
        return self.get_user_initiated_ratio() < 0.3

    def is_user_mostly_active(self) -> bool:
        """用户是否主要是主动发起"""
        return self.get_user_initiated_ratio() > 0.7

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "user_initiated_count": self.state.user_initiated_count,
            "consecutive_proactive_count": self.state.consecutive_proactive_count,
            "user_initiated_ratio": self.get_user_initiated_ratio(),
            "activity_level": self.get_activity_level().value,
            "idle_hours": self.get_idle_hours(),
            "message_count_today": self.state.message_count_today,
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self.state.user_initiated_count = 0
        self.state.consecutive_proactive_count = 0
        self.state.user_response_count = 0
        self._save_state()


def get_user_service() -> UserService:
    """获取用户服务实例"""
    return UserService.get_instance()
