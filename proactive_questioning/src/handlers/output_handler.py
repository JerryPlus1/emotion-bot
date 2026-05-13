"""输出处理器。

格式化输出消息。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime


class OutputHandler:
    """输出处理器"""

    def __init__(self):
        self.max_content_length = 5000  # 最大内容长度

    def format_assistant_message(self, content: str) -> str:
        """格式化助手消息"""
        return content

    def format_reading_content(
        self,
        chapter_info: str,
        content: str,
        show_header: bool = True,
    ) -> str:
        """格式化朗读内容"""
        if show_header and chapter_info:
            return f"【{chapter_info}】\n\n{content}"
        return content

    def format_reminder_message(self, reminder_text: str) -> str:
        """格式化提醒消息"""
        return reminder_text

    def format_error_message(self, error: str) -> str:
        """格式化错误消息"""
        return f"抱歉，出现了一点问题：{error}"

    def format_timeout_message(self, timeout_seconds: int) -> str:
        """格式化超时消息"""
        return f"（用户超过 {timeout_seconds}s 无回应，本轮结束。）"

    def truncate_content(self, content: str, max_length: Optional[int] = None) -> str:
        """截断内容"""
        max_len = max_length or self.max_content_length
        if len(content) <= max_len:
            return content
        return content[:max_len] + "..."

    def format_system_info(self, messages: List[str]) -> str:
        """格式化系统信息"""
        return "\n".join(messages)

    def format_debug_info(self, key: str, value: Any) -> str:
        """格式化调试信息"""
        if isinstance(value, str):
            value_preview = value[:200] + "..." if len(value) > 200 else value
            return f"[DEBUG] {key}: {value_preview}"
        return f"[DEBUG] {key}: {value}"

    def format_welcome_message(self) -> str:
        """格式化欢迎消息"""
        return """欢迎使用 AI 主动提问系统！
        
我可以主动和你聊天，也可以帮你：
- 记住重要的事情和生日
- 在适当的时候提醒你
- 陪你聊天、读小说

有什么想聊的吗？"""

    def format_reminder_added(self, description: str, date: str) -> str:
        """格式化提醒添加确认"""
        return f"好的，我记下了：{description}（{date}）"

    def format_birthday_greeting(self, person_name: str) -> str:
        """格式化生日祝福"""
        if person_name:
            return f"生日快乐，{person_name}！🎂"
        return "生日快乐！🎂"


def get_output_handler() -> OutputHandler:
    """获取输出处理器"""
    return OutputHandler()
