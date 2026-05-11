"""Local LLM adapter for the GGUF model under the model directory."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from .config import AppSettings

LOGGER = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


@dataclass
class GenerationOptions:
    max_tokens: int
    temperature: float
    top_p: float


class BaseLLM:
    backend_name = "base"

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        raise NotImplementedError

    def generate_chat(self, messages: list[dict[str, str]], options: GenerationOptions) -> str:
        prompt = "\n".join(f"{message['role']}：{message['content']}" for message in messages)
        return self.generate(f"{prompt}\nassistant：", options)


class MockLLM(BaseLLM):
    """Deterministic fallback for tests and UI smoke checks."""

    backend_name = "mock"

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        del options
        last_user = prompt.rsplit("用户：", 1)[-1].split("\n", 1)[0].strip()
        if not last_user:
            last_user = "我收到你的消息了"
        return (
            "我已经收到你的消息。当前运行在 mock 模式，说明后端链路、记忆和前端都可以工作；"
            f"你刚才说的是：{last_user}"
        )

    def generate_chat(self, messages: list[dict[str, str]], options: GenerationOptions) -> str:
        del options
        last_user = ""
        for message in reversed(messages):
            if message["role"] == "user":
                last_user = message["content"].strip()
                break
        return (
            "我已经收到你的消息。当前运行在 mock 模式，说明后端链路、记忆和前端都可以工作；"
            f"你刚才说的是：{last_user or '空消息'}"
        )


class LlamaCppLLM(BaseLLM):
    backend_name = "llama-cpp-gguf"

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.model_path = settings.model_path
        self._model = None
        self._lock = Lock()

    def _load(self):
        if self._model is not None:
            return self._model
        if not self.model_path.exists():
            raise LLMError(f"模型文件不存在：{self.model_path}")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise LLMError(
                "未安装 llama-cpp-python。请先运行：pip install -r requirements.txt"
            ) from exc

        LOGGER.info("Loading GGUF model from %s", self.model_path)
        self._model = Llama(
            model_path=str(self.model_path),
            n_ctx=self.settings.n_ctx,
            n_threads=self.settings.n_threads,
            n_gpu_layers=self.settings.n_gpu_layers,
            n_batch=self.settings.n_batch,
            verbose=False,
        )
        return self._model

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        with self._lock:
            model = self._load()
            result = model(
                prompt,
                max_tokens=options.max_tokens,
                temperature=options.temperature,
                top_p=options.top_p,
                stop=["<|im_end|>", "<|endoftext|>", "\n用户："],
                echo=False,
            )
        text = result["choices"][0]["text"].strip()
        return text or "我在认真想，但这次没有生成出有效回复。你可以换一种说法再试试。"

    def generate_chat(self, messages: list[dict[str, str]], options: GenerationOptions) -> str:
        with self._lock:
            model = self._load()
            result: dict[str, Any] = model.create_chat_completion(
                messages=messages,
                max_tokens=options.max_tokens,
                temperature=options.temperature,
                top_p=options.top_p,
                stop=["<|im_end|>", "<|endoftext|>"],
            )
        text = result["choices"][0]["message"]["content"].strip()
        return text or "我在认真想，但这次没有生成出有效回复。你可以换一种说法再试试。"


def build_llm(settings: AppSettings) -> BaseLLM:
    backend = settings.llm_backend.lower()
    if backend == "mock":
        return MockLLM()
    if backend in {"auto", "llama-cpp", "llamacpp"}:
        if backend == "auto" and not Path(settings.model_path).exists():
            LOGGER.warning("Model file not found, falling back to mock backend: %s", settings.model_path)
            return MockLLM()
        return LlamaCppLLM(settings)
    raise LLMError(f"不支持的 EMOTION_BOT_LLM_BACKEND：{settings.llm_backend}")
