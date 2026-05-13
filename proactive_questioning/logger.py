"""统一日志模块，提供分级日志输出。"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from typing import Callable


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


# 全局日志级别，DEBUG 显示详细输出
_current_level = LogLevel.INFO

# 日志前缀样式
_PREFIXES = {
    LogLevel.DEBUG: "\033[36m[DEBUG]\033[0m",    # 青色
    LogLevel.INFO: "\033[32m[INFO]\033[0m",      # 绿色
    LogLevel.WARNING: "\033[33m[WARN]\033[0m",   # 黄色
    LogLevel.ERROR: "\033[31m[ERROR]\033[0m",   # 红色
}


def set_level(level: LogLevel) -> None:
    """设置日志级别。"""
    global _current_level
    _current_level = level


def debug(msg: str) -> None:
    """调试日志。"""
    _log(LogLevel.DEBUG, msg)


def info(msg: str) -> None:
    """信息日志。"""
    _log(LogLevel.INFO, msg)


def warning(msg: str) -> None:
    """警告日志。"""
    _log(LogLevel.WARNING, msg)


def error(msg: str) -> None:
    """错误日志。"""
    _log(LogLevel.ERROR, msg)


def _log(level: LogLevel, msg: str) -> None:
    """内部日志输出函数。"""
    if level.value < _current_level.value:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = _PREFIXES.get(level, "")
    print(f"{prefix} [{timestamp}] {msg}", file=sys.stdout)


# ──── 便捷日志函数 ─────────────────────────────────────────────────────────

def log_model_load(path: str) -> None:
    """模型加载日志。"""
    info(f"Loading model: {path}")


def log_model_success() -> None:
    """模型推理成功日志。"""
    debug("Model inference succeeded")


def log_model_error(err: str) -> None:
    """模型错误日志。"""
    error(f"Model inference failed: {err}")


def log_reminder_check(birthdays: int, events: int) -> None:
    """提醒检查日志。"""
    if birthdays > 0 or events > 0:
        info(f"Reminders: {birthdays} birthdays, {events} events due")
    else:
        debug("No reminders due")


def log_session_start(opening_type: str) -> None:
    """会话开始日志。"""
    info(f"Starting chat session (type: {opening_type})")
