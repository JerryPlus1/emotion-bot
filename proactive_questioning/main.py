"""AI 主动提问系统 - 增强版。

支持用户主动说话检测和智能调整策略。

目录结构:
    src/
        models/          # 数据模型
        services/        # 服务层
        handlers/        # 处理器
        utils/          # 工具函数
"""

import sys
import time
import threading
from pathlib import Path
from typing import Optional, Callable

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    CHAT_HISTORY_PATH,
    INTERVAL_SECONDS,
    SESSION_COOLDOWN_SECONDS,
    FORCE_ASK_AFTER_COOLDOWN,
)
from core.logger import info, debug, error
from core.store import (
    load_store,
    save_store,
    cooldown_blocks,
    seconds_until_cooldown_ok,
    messages_nonempty,
)

from core.services import (
    ChatService,
    ReminderService,
    ProactivityService,
    UserService,
)
from core.models.session import SessionType


def _get_msg_attr(m, key: str, default: str = "") -> str:
    """获取消息属性，兼容字典和ChatMessage对象"""
    if isinstance(m, dict):
        return m.get(key, default)
    if key == "role":
        return m.role.value if hasattr(m.role, 'value') else str(m.role)
    if key == "content":
        return m.content
    return default

class ProactiveChatSystem:
    """主动聊天系统"""

    def __init__(self):
        self.chat_service = ChatService()
        self.reminder_service = ReminderService.get_instance()
        self.proactivity_service = ProactivityService.get_instance()
        self.user_service = UserService.get_instance()

        # 用户主动说话相关
        self.user_active_threshold = 0.7  # 用户主动说话阈值
        self.adaptive_interval = True     # 是否启用自适应间隔

        # 回调
        self._callbacks = {
            "on_cycle": [],
            "on_session_start": [],
            "on_session_end": [],
            "on_user_spoke_first": [],
        }

    def register_callback(self, event: str, callback: Callable):
        """注册回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _trigger_callback(self, event: str, *args, **kwargs):
        """触发回调"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                error(f"回调执行失败: {e}")

    def run(self):
        """运行主循环"""
        info("Starting chat loop")

        self._print_banner()

        while True:
            try:
                self._cycle_once()
            except KeyboardInterrupt:
                info("Shutting down")
                print("\n已退出。")
                break
            except Exception as e:
                error(f"Cycle error: {e}")

            # 自适应间隔
            if self.adaptive_interval:
                interval = self._get_adaptive_interval()
            else:
                interval = INTERVAL_SECONDS

            time.sleep(interval)

    def _cycle_once(self):
        """单次检查循环"""
        messages, file_existed, last_end = load_store()

        # 触发周期回调
        self._trigger_callback("on_cycle")

        # 1. 检查用户主动输入
        user_spoke = self._check_user_spoke_first(messages)
        if user_spoke:
            self._trigger_callback("on_user_spoke_first", user_spoke)
            return  # 用户主动说话，不触发主动对话

        # 2. 启动关心（漏掉提醒）
        caring_msg, session_type = self._check_caring_on_start(messages, last_end)
        if caring_msg:
            self._run_session(messages, caring_msg, last_end, session_type)
            return

        # 3. 到期提醒检查
        reminder_msg, reminder_key, session_type = self._check_due_reminders()
        if reminder_msg:
            self._run_session(
                messages, reminder_msg, last_end, session_type,
                reminder_keys=[reminder_key] if reminder_key else None
            )
            return

        # 4. 触发判断
        trigger, reason = self._should_trigger(messages, file_existed, last_end)
        if not trigger:
            return

        # 5. 生成开场白
        question = self.proactivity_service.generate_proactive_question(messages)
        if not question:
            debug("Failed to generate question, skipping")
            return

        # 6. 执行会话
        self._run_session(messages, question, last_end, SessionType.QUESTION)

    def _check_user_spoke_first(self, messages: list) -> Optional[dict]:
        """检查用户是否主动说话"""
        if not messages:
            return None

        # 检查最后一条消息是否是用户消息
        for m in reversed(messages):
            role = _get_msg_attr(m, "role", "")
            content = _get_msg_attr(m, "content", "")

            if role == "assistant":
                break  # 遇到助手消息停止

            if role == "user" and content.strip():
                # 检查是否是在系统主动消息之后
                for prev in reversed(messages):
                    prev_role = _get_msg_attr(prev, "role", "")
                    if prev_role == "assistant":
                        prev_content = _get_msg_attr(prev, "content", "")
                        # 如果上一条是系统主动发起的对话
                        if self._is_proactive_opening(prev_content):
                            return {
                                "user_content": content,
                                "from_proactive": True,
                            }
                        break

                # 检查用户是否主动输入（不在主动消息后）
                return {
                    "user_content": content,
                    "from_proactive": False,
                }

        return None

    def _is_proactive_opening(self, content: str) -> bool:
        """判断内容是否是系统主动发起的对话"""
        # 常见主动对话特征
        proactive_patterns = [
            "最近怎么样", "你最近", "有什么开心", "忙吗",
            "好久没", "有什么想聊", "在忙什么",
        ]
        return any(p in content for p in proactive_patterns)

    def _check_caring_on_start(
        self,
        messages: list,
        last_end: Optional[float]
    ) -> tuple[Optional[str], Optional[SessionType]]:
        """检查启动时是否需要关心"""
        birthdays, events = self.reminder_service.get_missed_reminders()

        if not birthdays and not events:
            return None, None

        caring_msg = self.proactivity_service.generate_caring_message(birthdays, events)
        if not caring_msg:
            return None, None

        # 标记已提醒
        keys_to_mark = [
            f"bday:{date_str}" for _, date_str, _ in birthdays
        ] + [
            f"evt:{date_str}:{time_str or '00:00'}"
            for _, date_str, time_str in events
        ]
        self.reminder_service.mark_reminded(keys_to_mark)

        info(f"Caring on start: {caring_msg[:50]}...")
        return caring_msg, SessionType.CARING

    def _check_due_reminders(
        self
    ) -> tuple[Optional[str], Optional[str], Optional[SessionType]]:
        """检查到期提醒"""
        birthdays, events = self.reminder_service.get_due_reminders()

        if birthdays:
            birthday = birthdays[0]
            person_name = birthday.person_name or birthday.description
            greeting = f"生日快乐，{person_name}！🎂"
            key = f"bday:{birthday.date_str}"
            self.reminder_service.mark_reminded([key])
            return greeting, key, SessionType.BIRTHDAY

        if events:
            event = events[0]
            time_str = event.time_str or ""
            reminder_text = f"提醒：{event.description}"
            if time_str:
                reminder_text += f"（{time_str}）"
            key = f"evt:{event.date_str}:{time_str or '00:00'}"
            self.reminder_service.mark_reminded([key])
            return reminder_text, key, SessionType.EVENT

        return None, None, None

    def _should_trigger(
        self,
        messages: list,
        file_existed: bool,
        last_end: Optional[float]
    ) -> tuple[bool, str]:
        """判断是否应该触发会话"""
        # 无文件
        if not file_existed:
            return True, "new_file"

        # 空记录
        if not messages_nonempty(messages):
            return True, "empty_history"

        # 冷却中
        if cooldown_blocks(last_end):
            wait = int(seconds_until_cooldown_ok(last_end)) + 1
            debug(f"In cooldown, need to wait {wait}s more")
            return False, "in_cooldown"

        # 检查用户主动说话统计
        if self.user_service.is_user_mostly_active():
            debug("User mostly active, reducing proactive messages")
            # 用户很主动，减少主动
            if self.user_service.state.consecutive_proactive_count > 3:
                return False, "user_active"

        # 冷却结束强制触发
        if FORCE_ASK_AFTER_COOLDOWN:
            info("Cooldown complete, forcing question")
            return True, "force_after_cooldown"

        # 模型判断
        should_ask = self.proactivity_service.should_trigger_proactive(
            messages, True, False
        )
        return should_ask, "model_decision"

    def _run_session(
        self,
        messages: list,
        opening: str,
        last_end: Optional[float],
        session_type: SessionType,
        reminder_keys: Optional[list] = None,
    ):
        """执行会话"""
        info(f"Starting session (type={session_type.value})")

        # 触发会话开始回调
        self._trigger_callback("on_session_start", opening, session_type)

        # 运行会话
        session = self.chat_service.run_session(
            opening=opening,
            session_type=session_type,
            reminder_keys=reminder_keys,
        )

        # 更新消息
        messages = session.messages

        # 更新用户状态
        self.user_service.record_session_end()

        # 触发会话结束回调
        self._trigger_callback("on_session_end", session)

        info("Session completed")

    def _get_adaptive_interval(self) -> int:
        """获取自适应间隔"""
        base = INTERVAL_SECONDS
        return self.user_service.get_recommended_interval(base)

    def _print_banner(self):
        """打印横幅"""
        interval = self._get_adaptive_interval() if self.adaptive_interval else INTERVAL_SECONDS

        print(
            f"\n{'='*60}\n"
            f"  AI 主动提问系统 (增强版)\n"
            f"{'='*60}\n"
            f"  检查间隔: {interval}s (自适应)\n"
            f"  冷却时间: {SESSION_COOLDOWN_SECONDS}s\n"
            f"  触发策略: {'强制提问' if FORCE_ASK_AFTER_COOLDOWN else '模型判断'}\n"
            f"  历史文件: {CHAT_HISTORY_PATH}\n"
            f"  用户主动阈值: {self.user_active_threshold}\n"
            f"{'='*60}\n"
        )


def main():
    """主入口"""
    system = ProactiveChatSystem()
    system.run()


if __name__ == "__main__":
    main()
