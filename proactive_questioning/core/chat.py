"""
聊天会话模块：多轮对话、输入处理、结束判断。

用法:
    from chat import run_full_chat_session

    messages, end_ts = run_full_chat_session(messages, opening, last_end)
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Any

# 确保 UTF-8 输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from call_model import deepseek_chat
from config import (
    CHAT_SESSION_SYSTEM,
    SESSION_COOLDOWN_SECONDS,
    SESSION_IDLE_TIMEOUT_SECONDS,
    TOPIC_EXIT_SYSTEM,
    USE_TOPIC_EXIT_MODEL,
    RAG_ENABLED,
    RAG_TOP_K,
    RAG_MIN_SCORE,
    RAG_MAX_CONTEXT_LEN,
    RAG_CONTEXT_TEMPLATE,
    USE_LOCAL_MODEL,
    LOCAL_MODEL_TEMPERATURE,
    LOCAL_MODEL_MAX_TOKENS,
)
from core.logger import debug, info
from core.reminders import (
    add_birthday,
    add_event,
    check_due_reminders,
    extract_events_from_text,
    generate_birthday_greeting,
    generate_event_reminder,
    mark_reminded,
)
from core.store import save_store

# 延迟导入 RAG 和本地模型
_local_model = None


def _get_local_model():
    """获取本地模型实例"""
    global _local_model
    if _local_model is None:
        try:
            from core.local_model import get_local_model
            _local_model = get_local_model()
        except ImportError as e:
            debug(f"本地模型导入失败: {e}")
            _local_model = None
    return _local_model


def _get_rag_retriever():
    """获取 RAG 检索器"""
    try:
        from rag.rag_utils import get_rag_retriever
        return get_rag_retriever()
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════════════════════════════════════════

ChatMessage = dict[str, str]
SessionResult = tuple[list[ChatMessage], float | None]


# ═══════════════════════════════════════════════════════════════════════════════
# 结束语检测
# ═══════════════════════════════════════════════════════════════════════════════

_ROUND_END_EXACT_EN = frozenset({"exit", "quit", "/end", "q", "bye"})
_ROUND_END_EXACT_CN = frozenset({"结束", "拜拜", "回见", "再见"})
_ROUND_END_PHRASES = (
    "不想聊天", "不想聊了", "不想再聊", "不想说了", "不想讲了", "不想继续",
    "不聊了", "不讲了", "不说了", "别聊了", "别说了", "别问了",
    "先这样", "就这样吧", "到这儿吧", "到此为止", "结束聊天",
    "不用聊了", "不要聊了", "先挂了", "有空再聊", "改天再聊", "改天聊",
    "不想谈", "先忙了", "不打扰了",
)


def _is_round_end_keyword(user_line: str) -> bool:
    """检测显式结束语。"""
    t = user_line.strip()
    if not t:
        return False
    low = t.lower()
    if low in _ROUND_END_EXACT_EN or t in _ROUND_END_EXACT_CN:
        return True
    return any(phrase in t for phrase in _ROUND_END_PHRASES)


def should_end_by_topic(user_line: str, opening: str) -> bool:
    """
    使用模型判断是否应该结束对话。

    Args:
        user_line: 用户输入
        opening: 开场白

    Returns:
        True 表示应该结束
    """
    if not USE_TOPIC_EXIT_MODEL:
        return False

    reply = deepseek_chat(
        [
            {"role": "system", "content": TOPIC_EXIT_SYSTEM},
            {"role": "user", "content": f"开场白：{opening}\n用户说：{user_line}"},
        ],
        temperature=0.1,
        thinking=False,
    )

    if not reply:
        return False

    first = reply.strip().splitlines()[0].strip().upper()
    return first == "END"


# ═══════════════════════════════════════════════════════════════════════════════
# 消息构建
# ═══════════════════════════════════════════════════════════════════════════════

def _build_api_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """构建 API 调用消息列表。"""
    out: list[ChatMessage] = [{"role": "system", "content": CHAT_SESSION_SYSTEM}]
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        content = (m.get("content") or "").strip()
        if content:
            out.append({"role": role, "content": content})
    return out


def _build_rag_enhanced_system(user_input: str, messages: list = None) -> str:
    """
    构建带 RAG 增强的系统提示词。

    Args:
        user_input: 用户当前输入
        messages: 完整的对话历史（可选，用于补充上下文）

    Returns:
        增强后的系统提示词
    """
    if not RAG_ENABLED:
        return CHAT_SESSION_SYSTEM

    retriever = _get_rag_retriever()
    if retriever is None:
        return CHAT_SESSION_SYSTEM

    # 组合查询：如果有历史消息，拼接最近的用户输入
    query = user_input
    if messages:
        # 获取最近几轮对话作为上下文
        recent_msgs = messages[-6:] if len(messages) > 6 else messages
        context_lines = []
        for m in recent_msgs:
            if m.get("role") == "user":
                context_lines.append(m.get("content", ""))
            elif m.get("role") == "assistant":
                content = m.get("content", "")
                if len(content) > 100:
                    content = content[:100] + "..."
                context_lines.append(content)
        if context_lines:
            query = " | ".join(context_lines[-4:]) + " | " + user_input

    try:
        results = retriever.retrieve(
            query,
            top_k=RAG_TOP_K,
            min_score=RAG_MIN_SCORE,
        )

        if not results:
            return CHAT_SESSION_SYSTEM

        context = retriever.format_knowledge_context(
            results,
            max_len=RAG_MAX_CONTEXT_LEN,
        )

        print(f"[DEBUG] RAG 上下文长度: {len(context)} 字符")
        print(f"[DEBUG] RAG 上下文前200字: {context[:200]}...")

        enhanced_system = CHAT_SESSION_SYSTEM + RAG_CONTEXT_TEMPLATE.format(
            knowledge_context=context
        )
        return enhanced_system

    except Exception as e:
        debug(f"RAG 检索失败: {e}")
        return CHAT_SESSION_SYSTEM


# ═══════════════════════════════════════════════════════════════════════════════
# 带超时的输入
# ═══════════════════════════════════════════════════════════════════════════════

def _input_with_timeout(prompt: str) -> tuple[bool, str]:
    """
    带超时的输入，支持中文输入。

    Returns:
        (timed_out, user_line)
    """
    result: dict[str, Any] = {"value": ""}

    def _read():
        try:
            # 设置 stdin 编码为 UTF-8
            if hasattr(sys.stdin, 'reconfigure'):
                try:
                    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
                except Exception:
                    pass
            
            print(prompt, end="", flush=True)
            result["value"] = sys.stdin.readline().rstrip('\n')
        except Exception:
            pass

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=SESSION_IDLE_TIMEOUT_SECONDS)

    if t.is_alive():
        print()  # 换行
        return True, ""
    return False, result["value"]


# ═══════════════════════════════════════════════════════════════════════════════
# 朗读检测
# ═══════════════════════════════════════════════════════════════════════════════

_READ_KEYWORDS = ['读', '朗读', '念', '念一下', '读一下', '读读']

def _should_read_directly(user_input: str) -> bool:
    """检测用户是否要求朗读"""
    return any(kw in user_input for kw in _READ_KEYWORDS)


def _get_readable_content(user_input: str, retriever) -> str | None:
    """获取可直接朗读的内容"""
    if not retriever:
        return None

    import re

    # 书籍别名映射
    BOOK_ALIASES = {
        '红楼梦': 'hongloumeng',
        '石头记': 'hongloumeng',
    }

    # 识别书名
    book_name = None
    for alias in BOOK_ALIASES.keys():
        if alias in user_input:
            book_name = alias
            break

    if not book_name:
        return None

    # 提取章节号（支持中文和阿拉伯数字）
    # 模式: 第X回、第X章
    match = re.search(r'第([一二三四五六七八九十百千万\d]+)[回章节篇]', user_input)
    if not match:
        return None

    chapter_str = match.group(1)

    # 中文数字转换（修复版）
    def parse_cn_num(s):
        if s.isdigit():
            return int(s)

        cn_nums_map = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000,
        }

        result = 0
        temp = 0

        for char in s:
            if char in cn_nums_map:
                val = cn_nums_map[char]
                if val >= 100:
                    # 百、千、万：result = (result + temp) * val
                    result = (result + temp) * val
                    temp = 0
                elif val == 10:
                    # 十：如果前面有数字(temp)，乘以10；如果没有，等于10
                    if temp > 0:
                        result = result * 10 + temp * 10
                    else:
                        result = result * 10 if result else 10
                    temp = 0
                elif val > 0:
                    # 一~九：累加到temp
                    temp += val
                # 零跳过
            elif char.isdigit():
                temp = temp * 10 + int(char)

        return result + temp

    # 使用章节感知检索
    results = retriever._chapter_aware_retrieve(user_input, top_k=1)
    if not results:
        # 备选：使用语义检索
        query = f"{book_name}第{chapter_num}回"
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
        else:
            return full_content

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 提醒检测（会话中）
# ═══════════════════════════════════════════════════════════════════════════════

def _check_and_announce_reminders(
    messages: list[ChatMessage],
    last_end: float | None,
) -> bool:
    """
    检查并播报到期提醒。

    Returns:
        True 表示有提醒播报
    """
    birthdays, events = check_due_reminders()
    if not birthdays and not events:
        return False

    reminder_keys: list[str] = []

    if birthdays:
        desc = birthdays[0][2]
        reminder_text = generate_birthday_greeting(desc) or f"生日快乐，{desc}！"
        reminder_keys.append(f"bday:{birthdays[0][1]}")
    elif events:
        desc = events[0][0]
        date_str = events[0][1]
        time_str = events[0][2]
        reminder_text = (
            generate_event_reminder(desc, date_str, time_str)
            or f"提醒：{desc}（{date_str}）"
        )
        reminder_keys.append(f"evt:{date_str}:{time_str or '00:00'}")

    reminder_text = reminder_text.strip()
    print(f"\n[助手] {reminder_text}\n")
    messages.append({"role": "assistant", "content": reminder_text})
    save_store(messages, last_end)
    mark_reminded(reminder_keys)
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 核心会话函数
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_chat_session(
    messages: list[ChatMessage],
    opening: str,
    last_session_end_ts: float | None,
) -> SessionResult:
    """
    执行多轮聊天会话。

    Args:
        messages: 历史消息列表
        opening: 开场白
        last_session_end_ts: 上次会话结束时间戳

    Returns:
        (更新后的消息列表, 本次会话结束时间戳)
    """
    messages = list(messages)
    opening = opening.strip()
    messages.append({"role": "assistant", "content": opening})
    save_store(messages, last_session_end_ts)

    info(f"Session started: {opening[:50]}...")
    print(f"\n[助手] {opening}\n")
    print(
        f"（本轮多轮对话；说「不想聊了」「结束」等可主动结束，"
        f"或超过 {SESSION_IDLE_TIMEOUT_SECONDS}s 无回应自动结束；"
        f"结束后需冷却 {SESSION_COOLDOWN_SECONDS}s）\n"
    )

    while True:
        # 检查会话中期提醒
        _check_and_announce_reminders(messages, last_session_end_ts)

        # 获取用户输入
        timed_out, user_line = _input_with_timeout("[用户] ")
        if timed_out:
            ended_ts = time.time()
            messages.append(
                {"role": "assistant", "content": f"（用户超过 {SESSION_IDLE_TIMEOUT_SECONDS}s 无回应，本轮结束。）"}
            )
            save_store(messages, ended_ts)
            info("Session ended: user timeout")
            print(f"（用户超时 {SESSION_IDLE_TIMEOUT_SECONDS}s，本轮结束。）\n")
            return messages, ended_ts

        user_line = user_line.strip()
        if not user_line:
            print(f"（请输入内容，或说「结束」等词；超时 {SESSION_IDLE_TIMEOUT_SECONDS}s 将自动结束）")
            continue

        # 提取并记录事件
        extracted = extract_events_from_text(user_line)
        for ev in extracted:
            t = ev.get("type", "event")
            desc = (ev.get("description") or "").strip()
            date_str = (ev.get("date") or "").strip()
            time_str = ev.get("time")
            if t == "birthday":
                add_birthday(date_str, desc)
            else:
                add_event(date_str, time_str, desc)

        # 检查结束条件
        if _is_round_end_keyword(user_line):
            messages.append({"role": "user", "content": user_line})
            save_store(messages, last_session_end_ts)
            info("Session ended: explicit keyword")
            break

        if should_end_by_topic(user_line, opening):
            messages.append({"role": "user", "content": user_line})
            save_store(messages, last_session_end_ts)
            info("Session ended: topic model")
            print("（已判定结束本轮话题）\n")
            break

        # 正常对话
        messages.append({"role": "user", "content": user_line})
        save_store(messages, last_session_end_ts)

        # 检测"读"关键词，直接返回原文
        retriever = _get_rag_retriever()
        if _should_read_directly(user_line):
            reply = _get_readable_content(user_line, retriever)
            if reply:
                messages.append({"role": "assistant", "content": reply})
                print(f"\n[助手] {reply}\n")
                save_store(messages, last_session_end_ts)
                continue

        # 构建消息并获取回复
        if USE_LOCAL_MODEL:
            local_model = _get_local_model()
            if local_model is not None:
                # 使用本地模型 + RAG
                enhanced_system = _build_rag_enhanced_system(user_line, messages)
                reply = local_model.chat(
                    messages=messages,
                    system_prompt=enhanced_system,
                    max_new_tokens=LOCAL_MODEL_MAX_TOKENS,
                    temperature=LOCAL_MODEL_TEMPERATURE,
                )
            else:
                # 回退到 API
                api_msgs = _build_api_messages(messages)
                reply = deepseek_chat(api_msgs, temperature=0.7, thinking=False)
        else:
            # API + RAG 增强
            enhanced_system = _build_rag_enhanced_system(user_line, messages)
            api_msgs = [{"role": "system", "content": enhanced_system}]
            for m in messages:
                if m.get("role") in ("user", "assistant"):
                    api_msgs.append(m)
            reply = deepseek_chat(api_msgs, temperature=0.7, thinking=False)

        if not reply or not reply.strip():
            info("Session ended: empty response")
            print("模型无回复，结束本轮。")
            break

        reply = reply.strip()
        messages.append({"role": "assistant", "content": reply})
        print(f"\n[助手] {reply}\n")
        save_store(messages, last_session_end_ts)

    ended_ts = time.time()
    save_store(messages, ended_ts)
    info("Session ended normally")
    return messages, ended_ts
