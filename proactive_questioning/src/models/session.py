"""会话数据模型。

定义聊天会话结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from .message import ChatMessage


class SessionType(str, Enum):
    """会话类型"""
    CARING = "caring"        # 关心问候
    BIRTHDAY = "birthday"    # 生日提醒
    EVENT = "event"          # 事件提醒
    QUESTION = "question"    # 主动提问
    USER_TRIGGERED = "user_triggered"  # 用户主动触发


class SessionState(str, Enum):
    """会话状态"""
    PENDING = "pending"      # 待开始
    ACTIVE = "active"        # 进行中
    COMPLETED = "completed"  # 已完成
    TIMEOUT = "timeout"     # 超时结束
    USER_ENDED = "user_ended"  # 用户主动结束


@dataclass
class ChatSession:
    """聊天会话"""
    session_type: SessionType
    opening: str
    state: SessionState = SessionState.PENDING
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    reminder_keys: List[str] = field(default_factory=list)

    def start(self) -> None:
        """开始会话"""
        self.state = SessionState.ACTIVE

    def add_message(self, message: ChatMessage) -> None:
        """添加消息"""
        self.messages.append(message)

    def add_user_message(self, content: str) -> ChatMessage:
        """添加用户消息"""
        msg = ChatMessage(role=MessageRole.USER, content=content)
        self.messages.append(msg)
        return msg

    def add_assistant_message(self, content: str) -> ChatMessage:
        """添加助手消息"""
        msg = ChatMessage(role=MessageRole.ASSISTANT, content=content)
        self.messages.append(msg)
        return msg

    def end(self, state: SessionState = SessionState.COMPLETED) -> None:
        """结束会话"""
        self.state = state
        self.ended_at = datetime.now()

    def get_duration(self) -> Optional[float]:
        """获取会话持续时间（秒）"""
        if self.ended_at:
            return (self.ended_at - self.created_at).total_seconds()
        return None

    def get_user_messages(self) -> List[ChatMessage]:
        """获取所有用户消息"""
        return [m for m in self.messages if m.is_user()]

    def get_last_user_message(self) -> Optional[ChatMessage]:
        """获取最后一条用户消息"""
        user_msgs = self.get_user_messages()
        return user_msgs[-1] if user_msgs else None

    def get_turn_count(self) -> int:
        """获取对话轮次"""
        return len(self.get_user_messages())

    def is_active(self) -> bool:
        """是否进行中"""
        return self.state == SessionState.ACTIVE

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": self.session_type.value,
            "state": self.state.value,
            "opening": self.opening,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "reminder_keys": self.reminder_keys,
        }


# 重新导入 MessageRole 以避免循环引用
from .message import MessageRole
