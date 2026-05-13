"""聊天服务。

管理聊天会话和消息处理。
"""

import threading
import sys
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.message import ChatMessage, MessageRole
from src.models.session import ChatSession, SessionType, SessionState
from src.services.llm_service import get_llm_service
from src.services.user_service import get_user_service
from src.services.reminder_service import get_reminder_service
from config import (
    CHAT_SESSION_SYSTEM,
    SESSION_COOLDOWN_SECONDS,
    SESSION_IDLE_TIMEOUT_SECONDS,
    RAG_ENABLED,
    RAG_TOP_K,
    RAG_MIN_SCORE,
    RAG_MAX_CONTEXT_LEN,
)
from logger import debug, info, error


# 结束关键词
_ROUND_END_KEYWORDS = frozenset({
    "结束", "拜拜", "回见", "再见", "不聊了", "不说了", "不想聊了",
    "先这样", "就这样吧", "先挂了", "不想说了", "不想聊了",
})

# 朗读关键词
_READ_KEYWORDS = ["读", "朗读", "念", "念一下", "读一下", "读读"]


class ChatService:
    """聊天服务"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.user_service = get_user_service()
        self.reminder_service = get_reminder_service()
        self.rag_retriever = None

        # 回调函数
        self.on_message: Optional[Callable] = None
        self.on_session_end: Optional[Callable] = None

    def _get_rag_retriever(self):
        """获取RAG检索器"""
        if self.rag_retriever is None:
            try:
                from ...rag_utils import get_rag_retriever
                self.rag_retriever = get_rag_retriever()
            except Exception as e:
                debug(f"RAG检索器加载失败: {e}")
        return self.rag_retriever

    def run_session(
        self,
        opening: str,
        session_type: SessionType = SessionType.QUESTION,
        reminder_keys: Optional[List[str]] = None,
    ) -> ChatSession:
        """运行聊天会话"""
        session = ChatSession(
            session_type=session_type,
            opening=opening,
        )
        session.start()

        # 标记提醒
        if reminder_keys:
            session.reminder_keys = reminder_keys
            self.reminder_service.mark_reminded(reminder_keys)

        # 记录主动消息
        if session_type == SessionType.QUESTION:
            self.user_service.record_proactive_message()

        # 记录会话结束回调
        def on_end(state: SessionState):
            session.end(state)
            self.user_service.record_session_end()
            if self.on_session_end:
                self.on_session_end(session)

        # 主循环
        self._session_loop(session, on_end)

        return session

    def _session_loop(
        self,
        session: ChatSession,
        on_end: Callable,
    ) -> None:
        """会话主循环"""
        # 打印开场白
        session.add_assistant_message(session.opening)
        print(f"\n[助手] {session.opening}\n")
        print(f"（本轮多轮对话；说「不想聊了」「结束」等可主动结束，")
        print(f"或超过 {SESSION_IDLE_TIMEOUT_SECONDS}s 无回应自动结束；")
        print(f"结束后需冷却 {SESSION_COOLDOWN_SECONDS}s）\n")

        while True:
            # 检查提醒
            self._check_and_announce_reminders(session)

            # 获取用户输入
            timed_out, user_line = self._input_with_timeout("[用户] ")

            if timed_out:
                session.add_assistant_message(f"（用户超过 {SESSION_IDLE_TIMEOUT_SECONDS}s 无回应，本轮结束。）")
                print(f"（用户超时 {SESSION_IDLE_TIMEOUT_SECONDS}s，本轮结束。）\n")
                on_end(SessionState.TIMEOUT)
                return

            user_line = user_line.strip()
            if not user_line:
                print(f"（请输入内容，或说「结束」等词）")
                continue

            # 记录用户消息
            session.add_user_message(user_line)

            # 提取事件
            self._extract_events(user_line)

            # 检查结束条件
            if self._should_end(user_line, session.opening):
                on_end(SessionState.USER_ENDED)
                return

            # 处理朗读请求
            if self._should_read(user_line):
                content = self._get_readable_content(user_line)
                if content:
                    session.add_assistant_message(content)
                    print(f"\n[助手] {content}\n")
                    continue

            # 生成回复
            reply = self._generate_reply(session.messages)

            if not reply or not reply.strip():
                error("模型无回复")
                on_end(SessionState.COMPLETED)
                return

            # 记录并输出回复
            session.add_assistant_message(reply)
            print(f"\n[助手] {reply}\n")

    def _should_end(self, user_input: str, opening: str) -> bool:
        """判断是否应结束"""
        # 关键词检查
        for keyword in _ROUND_END_KEYWORDS:
            if keyword in user_input:
                return True

        # 尝试使用主动服务判断
        try:
            from .proactivity_service import get_proactivity_service
            proactivity = get_proactivity_service()
            if proactivity.should_end_conversation(user_input, opening):
                return True
        except Exception:
            pass

        return False

    def _should_read(self, user_input: str) -> bool:
        """判断是否朗读请求"""
        return any(kw in user_input for kw in _READ_KEYWORDS)

    def _get_readable_content(self, user_input: str) -> Optional[str]:
        """获取可朗读内容"""
        retriever = self._get_rag_retriever()
        if not retriever:
            return None

        # 使用RAG的章节感知检索
        try:
            results = retriever._chapter_aware_retrieve(user_input, top_k=1)
            if not results:
                query = user_input
                results = retriever.retrieve(query, top_k=3, min_score=0.1)

            if results:
                contents = []
                chapter_info = ""
                for r in results:
                    if chapter_info == "":
                        chapter_info = r.get('chapter_info', '')
                    contents.append(r['content'])

                full_content = "\n\n".join(contents)

                if chapter_info:
                    return f"【{chapter_info}】\n\n{full_content}"
                return full_content
        except Exception as e:
            debug(f"获取可朗读内容失败: {e}")

        return None

    def _generate_reply(self, messages: list) -> Optional[str]:
        """生成回复"""
        # 构建系统提示词
        system_prompt = CHAT_SESSION_SYSTEM

        # RAG增强
        if RAG_ENABLED:
            retriever = self._get_rag_retriever()
            if retriever:
                context = self._build_rag_context(messages, retriever)
                if context:
                    system_prompt += f"\n\n=== 原文内容 ===\n{context}\n=== 原文结束 ===\n"
                    system_prompt += "\n当用户要求\"读\"时，直接输出原文。"

        # 构建消息
        api_messages = []
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                api_messages.append({
                    "role": m.get("role"),
                    "content": m.get("content", ""),
                })

        # 调用LLM
        reply = self.llm_service.chat(
            messages=api_messages,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2048,
        )

        # 移除<think>
        if reply:
            import re
            reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
            reply = reply.strip()

        return reply

    def _build_rag_context(self, messages: list, retriever) -> str:
        """构建RAG上下文"""
        try:
            user_input = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    user_input = m.get("content", "")
                    break

            if not user_input:
                return ""

            results = retriever.retrieve(
                user_input,
                top_k=RAG_TOP_K,
                min_score=RAG_MIN_SCORE,
            )

            if not results:
                return ""

            debug(f"RAG 上下文长度: {len(results)} 条结果")

            context_parts = []
            for r in results:
                content = r.get("content", "")
                metadata = r.get("metadata", {})
                source = metadata.get("source", "")
                context_parts.append(f"【{source}】\n{content}")

            return "\n\n".join(context_parts)[:RAG_MAX_CONTEXT_LEN]

        except Exception as e:
            debug(f"RAG上下文构建失败: {e}")
            return ""

    def _check_and_announce_reminders(self, session: ChatSession) -> None:
        """检查并播报提醒"""
        birthdays, events = self.reminder_service.get_due_reminders()

        if not birthdays and not events:
            return

        if birthdays:
            birthday = birthdays[0]
            greeting = f"生日快乐，{birthday.person_name or birthday.description}！🎂"
            key = f"bday:{birthday.date_str}"
        else:
            event = events[0]
            greeting = f"提醒：{event.description}"
            time_str = event.time_str or "00:00"
            key = f"evt:{event.date_str}:{time_str}"

        session.add_assistant_message(greeting)
        print(f"\n[助手] {greeting}\n")

        self.reminder_service.mark_reminded([key])

    def _extract_events(self, text: str) -> None:
        """提取文本中的事件"""
        try:
            from ...reminders import extract_events_from_text

            events = extract_events_from_text(text)
            for ev in events:
                ev_type = ev.get("type", "event")
                desc = ev.get("description", "").strip()
                date_str = ev.get("date", "").strip()
                time_str = ev.get("time")

                if ev_type == "birthday":
                    self.reminder_service.add_birthday(date_str, desc)
                elif date_str:
                    self.reminder_service.add_event(date_str, time_str or "", desc)

        except Exception as e:
            debug(f"事件提取失败: {e}")

    def _input_with_timeout(self, prompt: str) -> tuple:
        """带超时的输入"""
        result = {"value": ""}

        def read_input():
            try:
                if hasattr(sys.stdin, 'reconfigure'):
                    try:
                        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
                    except Exception:
                        pass
                print(prompt, end="", flush=True)
                result["value"] = sys.stdin.readline().rstrip('\n')
            except Exception:
                pass

        t = threading.Thread(target=read_input, daemon=True)
        t.start()
        t.join(timeout=SESSION_IDLE_TIMEOUT_SECONDS)

        if t.is_alive():
            print()
            return True, ""
        return False, result["value"]


def get_chat_service() -> ChatService:
    """获取聊天服务"""
    return ChatService()
