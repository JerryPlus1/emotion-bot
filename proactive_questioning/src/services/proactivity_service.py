"""主动服务。

管理主动对话触发和生成逻辑（本地模型版本）。
"""

from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.reminder_service import get_reminder_service
from src.services.user_service import get_user_service
from src.services.llm_service import get_llm_service
from src.models.session import SessionType
from config import QUESTION_SYSTEM
from logger import debug, info


class ProactivityService:
    """主动对话服务"""

    _instance: Optional["ProactivityService"] = None

    def __init__(self):
        self.reminder_service = get_reminder_service()
        self.user_service = get_user_service()
        self.llm_service = get_llm_service()

    @classmethod
    def get_instance(cls) -> "ProactivityService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def check_missed_reminders(self) -> Tuple[Optional[str], Optional[SessionType]]:
        """检查漏掉的提醒"""
        birthdays, events = self.reminder_service.get_missed_reminders()

        if birthdays or events:
            caring_msg = self._generate_caring_message(birthdays, events)
            return caring_msg, SessionType.CARING

        return None, None

    def check_due_reminders(self) -> Tuple[Optional[str], Optional[str], Optional[SessionType]]:
        """检查到期提醒"""
        birthdays, events = self.reminder_service.get_due_reminders()

        if birthdays:
            birthday = birthdays[0]
            greeting = f"生日快乐，{birthday.person_name or birthday.description}！🎂"
            key = f"bday:{birthday.date_str}"
            return greeting, key, SessionType.BIRTHDAY

        if events:
            event = events[0]
            time_str = event.time_str or ""
            reminder_text = f"提醒：{event.description}"
            if time_str:
                reminder_text += f"（{time_str}）"
            key = f"evt:{event.date_str}:{time_str or '00:00'}"
            return reminder_text, key, SessionType.EVENT

        return None, None, None

    def generate_proactive_question(self, messages: list) -> Optional[str]:
        """生成主动问题"""
        prompt = self._build_question_prompt(messages)
        reply = self.llm_service.generate(
            prompt=prompt,
            system_prompt=QUESTION_SYSTEM,
            temperature=0.8,
            max_tokens=256,
        )

        if reply:
            reply = reply.strip()
            return reply

        return None

    def should_end_conversation(self, user_input: str) -> bool:
        """判断是否应结束对话"""
        end_keywords = [
            "结束", "不聊了", "拜拜", "回见", "再见",
            "不想聊了", "先这样", "先挂了", "不想说了",
        ]

        for keyword in end_keywords:
            if keyword in user_input:
                return True

        return False

    def _generate_caring_message(self, birthdays: list, events: list) -> str:
        """生成关心消息"""
        parts = []

        if birthdays:
            names = [b[0] for b in birthdays if b[0]]
            if names:
                parts.append(f"{'、'.join(names)}的生日好像过了呢")
            else:
                parts.append("有朋友生日好像过了哦")

        if events:
            event_names = [e[0] for e in events]
            parts.append(f"有些事情需要跟进：{'、'.join(event_names)}")

        if not parts:
            return "最近怎么样？有什么想聊的吗？"

        # 使用模型生成
        prompt = "你是用户的好闺蜜。根据以下信息生成一句关心的问候：\n" + "\n".join(parts)
        reply = self.llm_service.generate(
            prompt=prompt,
            system_prompt="你是用户贴心的好闺蜜，语气温暖真诚。",
            temperature=0.8,
            max_tokens=128,
        )

        return reply.strip() if reply else parts[0]

    def _build_question_prompt(self, messages: list) -> str:
        """构建问题生成提示"""
        if messages:
            recent = messages[-6:]
            context_lines = []
            for m in recent:
                role = m.get("role", "")
                content = m.get("content", "")[:100]
                if role == "user":
                    context_lines.append(f"用户：{content}")
                elif role == "assistant":
                    context_lines.append(f"助手：{content}")

            if context_lines:
                return "最近的对话：\n" + "\n".join(context_lines[-4:]) + "\n\n请像闺蜜聊天一样问一个自然的问题。"

        return "好久没聊天了，像朋友一样随便问问对方最近怎么样。"


def get_proactivity_service() -> ProactivityService:
    """获取主动服务实例"""
    return ProactivityService.get_instance()
