"""本地 GGUF 客户端，负责通过 llama-cpp-python 调用本地模型。"""

import os
import re
from pathlib import Path
from typing import Any

DEFAULT_MODEL_PATH = "../models/qwen35-2b-sft-merged-q4_k_m.gguf"
FALLBACK_RESPONSE = "我刚刚有点卡住了，但我还在。你可以再和我说一遍吗？"

_llm: Any | None = None
_loaded_model_path: str | None = None
_last_error: str | None = None


class LocalModelError(RuntimeError):
    """Raised when the required local GGUF model cannot produce a real reply."""


def _get_model_path() -> Path:
    """从环境变量读取模型路径，没有配置时使用项目默认 GGUF 路径。"""
    return Path(os.getenv("LOCAL_GGUF_MODEL_PATH", DEFAULT_MODEL_PATH))


def _get_context_size() -> int:
    """读取本地模型上下文长度，长 Prompt 需要比默认值更大的上下文。"""
    raw_value = os.getenv("LOCAL_GGUF_N_CTX", "4096")
    try:
        return max(1024, int(raw_value))
    except ValueError:
        return 4096


def _set_last_error(message: str | None) -> None:
    """记录最近一次本地模型错误，方便 API debug 面板展示。"""
    global _last_error
    _last_error = message


def get_last_error() -> str | None:
    """返回最近一次本地模型加载或推理错误。"""
    return _last_error


def _clean_generated_text(text: str) -> str:
    """清理模型可能输出的思考标签和多余空白。"""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.replace("<think>", "").replace("</think>", "")
    return text.strip()


def is_response_usable(text: str | None) -> bool:
    """判断本地模型输出是否适合直接展示给用户。"""
    if not text:
        return False

    stripped = text.strip()
    if not stripped or stripped == FALLBACK_RESPONSE:
        return False

    # 如果模型输出大量问号，通常说明分词或解码结果不可用。
    question_mark_count = stripped.count("?") + stripped.count("？")
    if question_mark_count >= max(8, len(stripped) // 3):
        return False

    # 这些通常是 prompt 泄漏或模型开始写解题过程，不能直接给用户看。
    hard_block_markers = [
        "请输入你的回复",
        "请根据以上信息",
        "输出仅 JSON",
        "只输出 JSON",
        "不要解释字段",
        "用户输入",
        "用户刚刚说",
        "当前场景",
        "输出要求",
        "不要 JSON",
        "不要 Markdown",
        "现在需要处理",
        "生成一个符合要求",
    ]
    if any(marker in stripped for marker in hard_block_markers):
        return False

    # 避免把模型的内部分析、字段说明或 prompt 内容直接展示给用户。
    analysis_markers = [
        "用户画像",
        "关系状态",
        "安全边界",
        "输出格式",
        "inner_emotion",
        "suggested_expression",
        "回复内容",
        "我需要",
        "策略是",
        "应该先",
        "考虑到",
        "比如",
        "首先",
        "根据",
        "所以",
    ]
    marker_hits = sum(1 for marker in analysis_markers if marker in stripped)
    if marker_hits >= 2:
        return False

    if len(stripped) > 180 and marker_hits >= 1:
        return False

    # 本项目默认中文陪伴，完全没有中文时通常不是理想结果。
    has_cjk = any("\u4e00" <= char <= "\u9fff" for char in stripped)
    if not has_cjk:
        return False

    return True


def _load_model() -> Any | None:
    """懒加载本地模型，避免每次请求都重复加载大模型。"""
    global _llm, _loaded_model_path

    model_path = _get_model_path()
    model_path_text = str(model_path)

    # 模型文件不存在时直接 fallback，避免服务启动或请求时崩溃。
    if not model_path.is_file():
        _set_last_error(f"模型文件不存在: {model_path_text}")
        return None

    # 已经加载过同一路径时复用实例。
    if _llm is not None and _loaded_model_path == model_path_text:
        return _llm

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        _set_last_error(f"llama-cpp-python 未安装: {exc}")
        return None

    try:
        _llm = Llama(
            model_path=model_path_text,
            n_ctx=_get_context_size(),
            n_batch=512,
            verbose=False,
        )
        _loaded_model_path = model_path_text
        _set_last_error(None)
    except Exception as exc:  # noqa: BLE001 - 本地模型失败必须兜底，不能拖垮服务。
        _llm = None
        _loaded_model_path = None
        _set_last_error(f"模型加载失败: {exc}")
        return None

    return _llm


def is_local_model_available() -> bool:
    """返回本地模型路径和 llama-cpp-python 是否具备基础可用条件。"""
    model_path = _get_model_path()
    if not model_path.is_file():
        return False

    try:
        import llama_cpp  # noqa: F401
    except ImportError:
        return False

    return True


def generate_response(
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    use_mock_fallback: bool = True,
) -> str:
    """调用本地 GGUF 模型生成回复；失败时抛错，不返回假数据。"""
    _ = use_mock_fallback

    llm = _load_model()
    if llm is None:
        raise LocalModelError(get_last_error() or "本地模型不可用")

    try:
        result = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "<|im_end|>", "<|endoftext|>"],
        )
        text = _clean_generated_text(result["choices"][0]["text"])
        _set_last_error(None)
    except Exception as exc:  # noqa: BLE001 - 必须暴露真实本地模型失败，不能返回假数据。
        _set_last_error(f"模型推理失败: {exc}")
        raise LocalModelError(get_last_error() or "模型推理失败") from exc

    if not text:
        _set_last_error("模型返回空文本")
        raise LocalModelError(get_last_error())

    return text
