"""聊天消息模型。

定义消息结构和角色。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        """从字典创建"""
        role = MessageRole(data.get("role", "user"))
        content = data.get("content", "")

        timestamp = data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now()

        metadata = {k: v for k, v in data.items()
                   if k not in ("role", "content", "timestamp")}

        return cls(role=role, content=content, timestamp=timestamp, metadata=metadata)

    def is_user(self) -> bool:
        """是否为用户消息"""
        return self.role == MessageRole.USER

    def is_assistant(self) -> bool:
        """是否为助手消息"""
        return self.role == MessageRole.ASSISTANT

    def is_system(self) -> bool:
        """是否为系统消息"""
        return self.role == MessageRole.SYSTEM

    def is_empty(self) -> bool:
        """是否为空消息"""
        return not self.content or not self.content.strip()

    def __str__(self) -> str:
        prefix = "用户" if self.is_user() else "助手"
        content = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{prefix}] {content}"
