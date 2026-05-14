"""
主动提问模块：判断是否提问、生成开场白。

用法:
    from proactivity import should_ask_question, generate_proactive_question

    # 判断是否需要主动提问
    if should_ask_question(messages):
        question = generate_proactive_question(messages)
"""

from __future__ import annotations

import re
import os
from typing import Any

from call_model import deepseek_chat
from config import (
    DECISION_SYSTEM,
    QUESTION_SYSTEM,
    RAG_ENABLED,
    RAG_TOP_K,
    RAG_MIN_SCORE,
    RAG_MAX_CONTEXT_LEN,
    RAG_CONTEXT_TEMPLATE,
    USE_LOCAL_MODEL,
    LOCAL_MODEL_TEMPERATURE,
    LOCAL_MODEL_MAX_TOKENS,
)
from core.logger import debug

# 延迟导入 RAG 模块
_rag_retriever = None


def _get_rag_retriever():
    """延迟加载 RAG 检索器"""
    global _rag_retriever
    if _rag_retriever is None:
        try:
            from rag.rag_utils import get_rag_retriever
            _rag_retriever = get_rag_retriever()
        except ImportError as e:
            debug(f"RAG 模块导入失败: {e}")
            _rag_retriever = None
    return _rag_retriever


def _get_local_model():
    """获取本地模型"""
    try:
        from core.local_model import get_local_model
        return get_local_model()
    except ImportError as e:
        debug(f"本地模型导入失败: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════════════════════════════════════════

ChatMessage = dict[str, str]


# ═══════════════════════════════════════════════════════════════════════════════
# 决策判断
# ═══════════════════════════════════════════════════════════════════════════════

def should_ask_question(messages: list[ChatMessage]) -> bool:
    """
    判断是否应该主动提问。

    Args:
        messages: 历史聊天记录

    Returns:
        True 表示应该提问，False 表示不提问
    """
    reply = deepseek_chat(
        [
            {"role": "system", "content": DECISION_SYSTEM},
            {
                "role": "user",
                "content": "以下为历史聊天记录：\n\n是否现在由助手主动提问？只回答 True 或 False。",
            },
        ],
        temperature=0.3,
        thinking=False,
    )
    debug(f"Ask decision: {reply}")
    return _parse_bool(reply)


def _parse_bool(text: str | None) -> bool:
    """解析布尔值响应。"""
    if not text:
        return False
    t = text.strip().splitlines()[0].strip().lower()
    if t.startswith("true") or t == "是" or t == "yes":
        return True
    if t.startswith("false") or t == "否" or t == "no":
        return False
    return bool(re.search(r"\btrue\b", t))


# ═══════════════════════════════════════════════════════════════════════════════
# 开场白生成
# ═══════════════════════════════════════════════════════════════════════════════

def generate_proactive_question(messages: list[ChatMessage]) -> str | None:
    """
    生成主动提问（像闺蜜日常闲聊）。

    Args:
        messages: 历史聊天记录

    Returns:
        生成的提问文本
    """
    # 1. 获取系统提示词
    system_prompt = QUESTION_SYSTEM
    
    # 2. 如果启用 RAG，检索相关知识
    user_content = "请生成一句日常闲聊的主动提问，像闺蜜聊天一样自然。"
    
    if RAG_ENABLED:
        retriever = _get_rag_retriever()
        if retriever is not None:
            try:
                # 从历史记录中提取关键词进行检索
                recent_topic = _extract_topic_from_history(messages)
                
                if recent_topic:
                    results = retriever.retrieve(
                        recent_topic,
                        top_k=RAG_TOP_K,
                        min_score=RAG_MIN_SCORE,
                    )
                    
                    if results:
                        context = retriever.format_knowledge_context(
                            results,
                            max_len=RAG_MAX_CONTEXT_LEN,
                        )
                        system_prompt = QUESTION_SYSTEM + RAG_CONTEXT_TEMPLATE.format(
                            knowledge_context=context
                        )
                        debug(f"RAG 检索到 {len(results)} 条相关知识")
            except Exception as e:
                debug(f"RAG 检索失败: {e}")
    
    # 3. 根据配置选择模型
    if USE_LOCAL_MODEL:
        local_model = _get_local_model()
        if local_model is not None:
            reply = local_model.chat(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                max_new_tokens=LOCAL_MODEL_MAX_TOKENS,
                temperature=LOCAL_MODEL_TEMPERATURE,
            )
            return reply.strip() if reply else None
    
    # 4. 回退到 DeepSeek API
    reply = deepseek_chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=LOCAL_MODEL_TEMPERATURE if USE_LOCAL_MODEL else 0.8,
        thinking=False,
    )
    return reply.strip() if reply else None


def _get_msg_attr(m, key: str, default: str = "") -> str:
    """获取消息属性，兼容字典和ChatMessage对象"""
    if isinstance(m, dict):
        return m.get(key, default)
    if key == "role":
        return m.role.value if hasattr(m.role, 'value') else str(m.role)
    if key == "content":
        return m.content
    return default

def _extract_topic_from_history(messages: list[ChatMessage]) -> str | None:
    """
    从历史记录中提取最近的话题关键词。

    Args:
        messages: 聊天历史

    Returns:
        提取的话题关键词
    """
    if not messages:
        return None
    
    # 获取最近几条用户消息
    recent_messages = []
    for msg in reversed(messages):
        role = _get_msg_attr(msg, "role")
        if role == "user":
            recent_messages.append(_get_msg_attr(msg, "content", ""))
            if len(recent_messages) >= 3:
                break
    
    if not recent_messages:
        return None
    
    # 拼接作为检索 query
    return " ".join(recent_messages[:2])[:100]  # 限制长度
