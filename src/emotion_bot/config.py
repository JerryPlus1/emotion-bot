"""Application configuration for the local emotion bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = (
    ROOT_DIR
    / "model"
    / "qwen-finetune-download"
    / "qwen35-2b-sft-merged-q4_k_m.gguf"
)


def _load_env_file() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _path_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value) if value else default
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


@dataclass(frozen=True)
class AppSettings:
    root_dir: Path = ROOT_DIR
    model_path: Path = _path_env("EMOTION_BOT_MODEL_PATH", DEFAULT_MODEL_PATH)
    data_dir: Path = _path_env("EMOTION_BOT_DATA_DIR", ROOT_DIR / "data")
    db_path: Path = _path_env("EMOTION_BOT_DB_PATH", ROOT_DIR / "data" / "emotion_bot.sqlite3")
    llm_backend: str = os.getenv("EMOTION_BOT_LLM_BACKEND", "auto")
    host: str = os.getenv("EMOTION_BOT_HOST", "127.0.0.1")
    port: int = _int_env("EMOTION_BOT_PORT", 8000)
    n_ctx: int = _int_env("EMOTION_BOT_N_CTX", 4096)
    n_threads: int = _int_env("EMOTION_BOT_N_THREADS", max(os.cpu_count() or 4, 4))
    n_gpu_layers: int = _int_env("EMOTION_BOT_N_GPU_LAYERS", 0)
    n_batch: int = _int_env("EMOTION_BOT_N_BATCH", 256)
    temperature: float = _float_env("EMOTION_BOT_TEMPERATURE", 0.72)
    top_p: float = _float_env("EMOTION_BOT_TOP_P", 0.9)
    max_tokens: int = _int_env("EMOTION_BOT_MAX_TOKENS", 512)
    auto_memory_threshold: float = _float_env("EMOTION_BOT_AUTO_MEMORY_THRESHOLD", 0.18)
    proactive_poll_seconds: int = _int_env("EMOTION_BOT_PROACTIVE_POLL_SECONDS", 45)


def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
