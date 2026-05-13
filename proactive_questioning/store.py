"""
聊天记录持久化模块。

用法:
    from store import load_store, save_store

    messages, existed, last_end = load_store()
    save_store(messages, timestamp)
"""

from __future__ import annotations

import json
import time
from typing import Any

from config import CHAT_HISTORY_PATH
from logger import debug, error

# ═══════════════════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════════════════

StoreData = dict[str, Any]
ChatMessage = dict[str, str]
LoadResult = tuple[list[ChatMessage], bool, float | None]


# ═══════════════════════════════════════════════════════════════════════════════
# 核心函数
# ═══════════════════════════════════════════════════════════════════════════════

def load_store() -> LoadResult:
    """
    加载聊天记录。

    Returns:
        (messages, file_existed, last_session_end_ts)
        - messages: 消息列表
        - file_existed: 历史文件是否存在
        - last_session_end_ts: 上次会话结束时间戳（None 表示无记录）
    """
    if not CHAT_HISTORY_PATH.exists():
        debug("History file not found, starting fresh")
        return [], False, None

    try:
        raw = CHAT_HISTORY_PATH.read_text(encoding="utf-8")
        if not raw.strip():
            return [], True, None

        obj = json.loads(raw)
        msgs = obj.get("messages", [])
        if not isinstance(msgs, list):
            msgs = []

        ts = obj.get("last_session_end_ts")
        last_end: float | None = None
        if ts is not None:
            try:
                last_end = float(ts)
            except (TypeError, ValueError):
                last_end = None

        return msgs, True, last_end

    except (json.JSONDecodeError, OSError) as e:
        error(f"Failed to load history: {e}")
        return [], True, None


def save_store(messages: list[ChatMessage], last_session_end_ts: float | None) -> None:
    """
    保存聊天记录。

    Args:
        messages: 消息列表
        last_session_end_ts: 会话结束时间戳
    """
    CHAT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    out: StoreData = {"messages": messages}
    if last_session_end_ts is not None:
        out["last_session_end_ts"] = last_session_end_ts

    CHAT_HISTORY_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    debug(f"Saved {len(messages)} messages")


def ensure_history_file_exists() -> None:
    """确保历史文件存在。"""
    if not CHAT_HISTORY_PATH.exists():
        save_store([], None)


# ═══════════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════════

def messages_nonempty(messages: list[ChatMessage]) -> bool:
    """检查消息列表是否有有效内容。"""
    return any(
        isinstance(m, dict) and (m.get("content") or "").strip()
        for m in messages
    )


def format_history_for_prompt(messages: list[ChatMessage]) -> str:
    """格式化聊天记录为提示文本。"""
    if not messages_nonempty(messages):
        return "(暂无聊天记录)"

    lines = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role", "")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        label = {"user": "用户", "assistant": "助手", "system": "系统"}.get(role, role)
        lines.append(f"{label}: {content}")

    return "\n".join(lines) if lines else "(暂无聊天记录)"


def cooldown_blocks(last_session_end_ts: float | None) -> bool:
    """检查是否仍在冷却期内。"""
    from config import SESSION_COOLDOWN_SECONDS
    if last_session_end_ts is None:
        return False
    return (time.time() - last_session_end_ts) < SESSION_COOLDOWN_SECONDS


def seconds_until_cooldown_ok(last_session_end_ts: float | None) -> float:
    """计算距离冷却结束还剩多少秒。"""
    from config import SESSION_COOLDOWN_SECONDS
    if last_session_end_ts is None:
        return 0.0
    need = SESSION_COOLDOWN_SECONDS - (time.time() - last_session_end_ts)
    return max(0.0, need)
