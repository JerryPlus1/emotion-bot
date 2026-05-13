"""提醒数据模型。

定义生日和事件提醒。
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from enum import Enum
from typing import Optional


class ReminderType(str, Enum):
    """提醒类型"""
    BIRTHDAY = "birthday"
    EVENT = "event"


@dataclass
class Reminder:
    """提醒基类"""
    reminder_type: ReminderType
    description: str
    date_str: str  # YYYY-MM-DD 或 MM-DD
    time_str: Optional[str] = None  # HH:MM
    created_at: datetime = field(default_factory=datetime.now)
    reminded: bool = False
    reminded_at: Optional[datetime] = None

    def get_display_text(self) -> str:
        """获取显示文本"""
        raise NotImplementedError

    def mark_reminded(self) -> None:
        """标记为已提醒"""
        self.reminded = True
        self.reminded_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": self.reminder_type.value,
            "description": self.description,
            "date": self.date_str,
            "time": self.time_str,
            "created_at": self.created_at.isoformat(),
            "reminded": self.reminded,
            "reminded_at": self.reminded_at.isoformat() if self.reminded_at else None,
        }


@dataclass
class BirthdayReminder(Reminder):
    """生日提醒"""
    person_name: str = ""

    def __post_init__(self):
        self.reminder_type = ReminderType.BIRTHDAY
        if not self.description:
            self.description = self.person_name or "生日"

    def get_display_text(self) -> str:
        """获取生日祝福文本"""
        if self.person_name:
            return f"{self.person_name}生日快乐！🎂"
        return "生日快乐！🎂"

    @classmethod
    def from_dict(cls, data: dict) -> "BirthdayReminder":
        """从字典创建"""
        return cls(
            description=data.get("description", ""),
            date_str=data.get("date", ""),
            person_name=data.get("person_name", ""),
            reminded=data.get("reminded", False),
        )


@dataclass
class EventReminder(Reminder):
    """事件提醒"""
    event_name: str = ""

    def __post_init__(self):
        self.reminder_type = ReminderType.EVENT
        if not self.description:
            self.description = self.event_name or "事件"

    def get_display_text(self) -> str:
        """获取事件提醒文本"""
        parts = []
        if self.time_str:
            parts.append(f"{self.time_str}")
        parts.append(self.description)
        return "提醒：" + " ".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> "EventReminder":
        """从字典创建"""
        return cls(
            description=data.get("description", ""),
            date_str=data.get("date", ""),
            time_str=data.get("time"),
            event_name=data.get("event_name", ""),
            reminded=data.get("reminded", False),
        )


def parse_reminder(data: dict) -> Reminder:
    """根据类型解析提醒"""
    reminder_type = data.get("type", "event")
    if reminder_type == ReminderType.BIRTHDAY.value:
        return BirthdayReminder.from_dict(data)
    return EventReminder.from_dict(data)
