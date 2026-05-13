"""提醒服务。

管理生日和事件提醒。
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.reminder import (
    Reminder,
    BirthdayReminder,
    EventReminder,
    ReminderType,
    parse_reminder,
)
from logger import debug, info


class ReminderService:
    """提醒服务"""

    _instance: Optional["ReminderService"] = None
    _reminders_file = Path(__file__).parent.parent.parent / "reminders.json"

    def __init__(self):
        self.reminders: List[Reminder] = self._load_reminders()

    @classmethod
    def get_instance(cls) -> "ReminderService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_reminders(self) -> List[Reminder]:
        """加载提醒"""
        if self._reminders_file.exists():
            try:
                with open(self._reminders_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [parse_reminder(r) for r in data.get("reminders", [])]
            except Exception as e:
                debug(f"加载提醒失败: {e}")
        return []

    def _save_reminders(self) -> None:
        """保存提醒"""
        try:
            data = {"reminders": [r.to_dict() for r in self.reminders]}
            with open(self._reminders_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            debug(f"保存提醒失败: {e}")

    def add_reminder(self, reminder: Reminder) -> None:
        """添加提醒"""
        self.reminders.append(reminder)
        self._save_reminders()
        info(f"添加提醒: {reminder.description} ({reminder.date_str})")

    def add_birthday(self, date_str: str, person_name: str = "") -> None:
        """添加生日提醒"""
        reminder = BirthdayReminder(
            date_str=date_str,
            person_name=person_name,
            description=person_name or "生日",
        )
        self.add_reminder(reminder)

    def add_event(self, date_str: str, time_str: str, event_name: str) -> None:
        """添加事件提醒"""
        reminder = EventReminder(
            date_str=date_str,
            time_str=time_str,
            event_name=event_name,
            description=event_name,
        )
        self.add_reminder(reminder)

    def remove_reminder(self, reminder_key: str) -> bool:
        """移除提醒"""
        original_count = len(self.reminders)
        self.reminders = [r for r in self.reminders if self._get_key(r) != reminder_key]
        if len(self.reminders) < original_count:
            self._save_reminders()
            return True
        return False

    def _get_key(self, reminder: Reminder) -> str:
        """获取提醒键"""
        if reminder.reminder_type == ReminderType.BIRTHDAY:
            return f"bday:{reminder.date_str}"
        else:
            time_str = reminder.time_str or "00:00"
            return f"evt:{reminder.date_str}:{time_str}"

    def get_due_reminders(self) -> Tuple[List[BirthdayReminder], List[EventReminder]]:
        """获取到期提醒"""
        birthdays = []
        events = []

        now = datetime.now()
        today_str = now.strftime("%m-%d")  # MM-DD 格式
        today_full = now.strftime("%Y-%m-%d")

        for reminder in self.reminders:
            if reminder.reminded:
                continue

            if reminder.reminder_type == ReminderType.BIRTHDAY:
                # 生日只比较月日
                if reminder.date_str.endswith(f"-{today_str}") or reminder.date_str == today_str:
                    birthdays.append(reminder)

            else:  # EVENT
                # 事件需要精确匹配
                if reminder.date_str == today_full:
                    events.append(reminder)

        return birthdays, events

    def get_missed_reminders(self) -> Tuple[List, List]:
        """获取漏掉的提醒"""
        birthdays = []
        events = []

        now = datetime.now()
        today = now.date()

        for reminder in self.reminders:
            if reminder.reminded:
                continue

            try:
                if reminder.reminder_type == ReminderType.BIRTHDAY:
                    # 解析月日
                    parts = reminder.date_str.split("-")
                    if len(parts) >= 2:
                        month, day = int(parts[-2]), int(parts[-1])
                        reminder_date = date(now.year, month, day)
                        if reminder_date < today:
                            birthdays.append((reminder.person_name, reminder.date_str, reminder.description))

                else:  # EVENT
                    reminder_date = datetime.fromisoformat(reminder.date_str).date()
                    if reminder_date < today:
                        events.append((reminder.description, reminder.date_str, reminder.time_str))

            except Exception:
                continue

        return birthdays, events

    def mark_reminded(self, keys: List[str]) -> None:
        """标记提醒为已提醒"""
        for reminder in self.reminders:
            key = self._get_key(reminder)
            if key in keys:
                reminder.mark_reminded()
        self._save_reminders()

    def clear_reminded(self) -> None:
        """清除已提醒的提醒"""
        self.reminders = [r for r in self.reminders if not r.reminded]
        self._save_reminders()

    def get_upcoming_reminders(self, days: int = 7) -> List[Reminder]:
        """获取即将到来的提醒"""
        upcoming = []
        now = datetime.now()

        for reminder in self.reminders:
            if reminder.reminded:
                continue

            try:
                if reminder.reminder_type == ReminderType.BIRTHDAY:
                    parts = reminder.date_str.split("-")
                    if len(parts) >= 2:
                        month, day = int(parts[-2]), int(parts[-1])
                        reminder_date = date(now.year, month, day)
                        days_until = (reminder_date - now.date()).days
                        if 0 <= days_until <= days:
                            upcoming.append(reminder)
            except Exception:
                continue

        return upcoming


def get_reminder_service() -> ReminderService:
    """获取提醒服务实例"""
    return ReminderService.get_instance()
