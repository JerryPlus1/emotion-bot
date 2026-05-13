"""
模型调用封装：本地 Qwen3 模型推理（支持 LoRA 微调模型）。

用法:
    from call_model import deepseek_chat

    # 普通调用（使用基础模型）
    response = deepseek_chat([{"role": "user", "content": "你好"}])

    # 禁用思考模式
    response = deepseek_chat(
        [{"role": "user", "content": "你好"}],
        thinking=False
    )
    
    # 使用训练好的模型（自动检测LoRA或合并模型）
    response = deepseek_chat([{"role": "user", "content": "你好"}])
"""

from __future__ import annotations

import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from config import MODEL_PATH, LORA_PATH, MERGED_MODEL_PATH
from logger import debug, error, info, warning

# ═══════════════════════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════════════════════

_tokenizer: AutoTokenizer | None = None
_model: AutoModelForCausalLM | None = None
_using_model_type: str = "base"  # "base", "lora", "merged"


# ═══════════════════════════════════════════════════════════════════════════════
# 模型路径检测
# ═══════════════════════════════════════════════════════════════════════════════

def _get_model_path() -> tuple[str, str]:
    """
    获取要使用的模型路径。
    
    优先级：
    1. 合并模型 (MERGED_MODEL_PATH)
    2. LoRA权重 (LORA_PATH) + 基础模型
    3. 基础模型 (MODEL_PATH)
    
    Returns:
        tuple[模型路径, 模型类型描述]
    """
    global _using_model_type
    
    # 优先使用合并模型
    if MERGED_MODEL_PATH and Path(MERGED_MODEL_PATH).exists():
        return MERGED_MODEL_PATH, "合并模型"
    
    # 其次使用LoRA权重
    if LORA_PATH and Path(LORA_PATH).exists():
        return MODEL_PATH, f"LoRA({LORA_PATH})"
    
    # 使用基础模型
    return MODEL_PATH, "基础模型"


# ═══════════════════════════════════════════════════════════════════════════════
# 模型加载
# ═══════════════════════════════════════════════════════════════════════════════

def _load_model() -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """懒加载模型和分词器（单例模式）。"""
    global _tokenizer, _model, _using_model_type
    
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer
    
    model_path, model_desc = _get_model_path()
    _using_model_type = model_desc
    
    info(f"Loading model: {model_path} ({model_desc})")
    
    # 加载tokenizer
    _tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    
    # 加载模型
    _model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    )
    
    # 如果是使用LoRA，加载LoRA权重
    if LORA_PATH and Path(LORA_PATH).exists() and MERGED_MODEL_PATH == "":
        try:
            from peft import PeftModel
            info(f"Loading LoRA weights: {LORA_PATH}")
            _model = PeftModel.from_pretrained(_model, LORA_PATH)
            _using_model_type = f"LoRA({LORA_PATH})"
            info("LoRA weights loaded successfully")
        except Exception as e:
            warning(f"Failed to load LoRA weights: {e}")
    
    _model.eval()
    info(f"Model loaded successfully ({_using_model_type})")
    
    return _model, _tokenizer


def reload_model() -> None:
    """重新加载模型和分词器。"""
    global _tokenizer, _model
    info("Reloading model...")
    _tokenizer = None
    _model = None
    _load_model()


def get_model_info() -> dict:
    """获取当前模型信息。"""
    _, model_desc = _get_model_path()
    return {
        "base_model": MODEL_PATH,
        "lora_path": LORA_PATH if LORA_PATH else None,
        "merged_path": MERGED_MODEL_PATH if MERGED_MODEL_PATH else None,
        "using": _using_model_type,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 核心推理函数
# ═══════════════════════════════════════════════════════════════════════════════

def deepseek_chat(
    messages: list[dict[str, str]],
    temperature: float | None = None,
    thinking: bool = True,
    max_new_tokens: int = 4096,
) -> str | None:
    """
    调用本地 Qwen3 模型生成回复。

    Args:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        temperature: 温度参数（None 时根据 thinking 自动设置）
        thinking: 是否启用思考模式（默认 True）
        max_new_tokens: 最大生成 token 数

    Returns:
        模型生成的文本，失败时返回 None
    """
    model, tokenizer = _load_model()

    # 确定采样参数
    temp = temperature if temperature is not None else (0.6 if thinking else 0.7)
    top_p = 0.95 if thinking else 0.8

    debug(f"Thinking: {thinking}, Temp: {temp}, TopP: {top_p}")

    try:
        # 构建对话模板
        chat_messages = list(messages)
        if not thinking:
            chat_messages = _add_no_think_suffix(chat_messages)

        # 格式化对话
        input_text = tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=thinking,
        )

        # Tokenize
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        # 生成配置
        gen_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temp,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                generation_config=gen_config,
            )

        # 解码
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=False)
        response_text = full_output[len(input_text):].replace(tokenizer.eos_token, "").strip()

        # 提取实际回复（去掉<think>思考过程）
        response_text = _extract_answer(response_text)

        if response_text:
            debug("Inference succeeded")
            return response_text

        error("Model returned empty response")
        return None

    except Exception as e:
        error(f"Inference failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_answer(text: str) -> str:
    """
    提取实际回复内容，去掉<think>思考过程。
    """
    import re
    
    # 移除所有<think>...</think>标签对（包含内容）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # 移除孤立的<think>开始标签
    text = re.sub(r'<think>', '', text)
    
    # 移除孤立的</think>结束标签
    text = re.sub(r'</think>', '', text)
    
    return text.strip()

def _add_no_think_suffix(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """为最后一条消息添加 /no_think 后缀。"""
    if not messages or messages[-1]["role"] != "user":
        return messages
    messages = list(messages)
    messages[-1] = {
        "role": messages[-1]["role"],
        "content": messages[-1]["content"] + " /no_think",
    }
    return messages
