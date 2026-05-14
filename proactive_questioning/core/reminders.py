"""
时间事件识别与提醒管理模块。

用法:
    from reminders import check_due_reminders, add_birthday, add_event

    # 检查到期提醒
    birthdays, events = check_due_reminders()

    # 添加生日
    add_birthday("04-15", "闺蜜小美")

    # 添加事件
    add_event("2024-04-20", "14:30", "去看牙医")
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import REMINDERS_PATH
from core.logger import debug, info

# ═══════════════════════════════════════════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════════════════════════════════════════

ReminderEntry = dict[str, Any]
ReminderData = dict[str, Any]
BirthdayTuple = tuple[str, str, str]  # (description, date_str, raw_desc)
EventTuple = tuple[str, str, str | None, str]  # (description, date_str, time_str, raw_desc)


# ═══════════════════════════════════════════════════════════════════════════════
# 时间工具
# ═══════════════════════════════════════════════════════════════════════════════

def _now_dt() -> datetime:
    """获取当前时间（本地时区）。"""
    return datetime.now().astimezone()


def _parse_dt(
    date_str: str,
    time_str: str | None,
    fallback_year: int | None = None,
) -> datetime | None:
    """
    解析日期字符串为 datetime。

    Args:
        date_str: YYYY-MM-DD 或 MM-DD 格式
        time_str: HH:MM[:SS] 格式
        fallback_year: MM-DD 格式时的备选年份

    Returns:
        解析后的 datetime，失败返回 None
    """
    now = _now_dt()
    year = fallback_year or now.year

    # 解析日期
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        _, month_str, day_str = date_str.split("-")
        year = int(_)
        month, day = int(month_str), int(day_str)
    elif re.match(r"^\d{2}-\d{2}$", date_str):
        month_str, day_str = date_str.split("-")
        month, day = int(month_str), int(day_str)
        candidate = now.replace(year=year, month=month, day=day)
        if candidate < now:
            year += 1
    else:
        return None

    # 解析时间
    if time_str and re.match(r"^\d{2}:\d{2}(:\d{2})?$", time_str):
        parts = [int(x) for x in time_str.split(":")]
        hour, minute, second = parts[0], parts[1], parts[2] if len(parts) == 3 else 0
    else:
        hour, minute, second = 9, 0, 0

    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=now.tzinfo)
    except ValueError:
        return None


def _next_occurrence(dt: datetime) -> datetime:
    """计算生日的最近一次到来（今年或明年）。"""
    now = _now_dt()
    this_yr = now.replace(month=dt.month, day=dt.day)
    return this_yr if this_yr > now else this_yr.replace(year=this_yr.year + 1)


def _relative_date(text: str) -> str | None:
    """将相对日期词转为 YYYY-MM-DD。"""
    text = (text or "").strip()
    if not text:
        return None
    now = _now_dt()
    if "后天" in text:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")
    if "明天" in text:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    if "今天" in text:
        return now.strftime("%Y-%m-%d")
    return None


def _parse_time(text: str) -> str | None:
    """从文本中提取时间。"""
    patterns = [
        (r"([01]?\d|2[0-3]):([0-5]\d):([0-5]\d)", "%02d:%02d:%02d"),
        (r"([01]?\d|2[0-3]):([0-5]\d)", "%02d:%02d"),
        (r"([01]?\d|2[0-3])点半", "%02d:30"),
        (r"([01]?\d|2[0-3])点", "%02d:00"),
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, text)
        if m:
            return fmt % int(m.group(1), 10)
    return None


def _parse_date(text: str) -> str | None:
    """从文本中提取日期。"""
    now = _now_dt()
    # 相对日期优先
    rel = _relative_date(text)
    if rel:
        return rel

    # 完整日期
    m = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d, tzinfo=now.tzinfo).strftime("%Y-%m-%d")
        except ValueError:
            return None

    # 月日
    m = re.search(r"(\d{1,2})月(\d{1,2})[日号]?", text)
    if m:
        mo, d = int(m.group(1)), int(m.group(2))
        try:
            candidate = datetime(now.year, mo, d, tzinfo=now.tzinfo)
        except ValueError:
            return None
        if candidate.date() < now.date():
            candidate = datetime(now.year + 1, mo, d, tzinfo=now.tzinfo)
        return candidate.strftime("%Y-%m-%d")
    return None


def _guess_description(text: str) -> str:
    """从文本中猜测事件描述。"""
    m = re.search(r"(提醒我|记得提醒我|记得|提醒)\s*(.+)", text)
    if m:
        desc = m.group(2).strip("，。,. ")
        return desc[:16] if desc else "日程"
    return "日程"


def _normalize_date(date_str: str | None, time_str: str | None) -> str | None:
    """标准化日期，处理时间跨天情况。"""
    now = _now_dt()
    if not date_str:
        base = now
        if time_str and re.match(r"^\d{2}:\d{2}(:\d{2})?$", time_str):
            parts = [int(x) for x in time_str.split(":")]
            hh, mm, ss = parts[0], parts[1], parts[2] if len(parts) == 3 else 0
            candidate = now.replace(hour=hh, minute=mm, second=ss, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate.strftime("%Y-%m-%d")
        return base.strftime("%Y-%m-%d")
    return date_str


def _parse_delay(text: str) -> int | None:
    """解析延迟时间（秒）。"""
    patterns = [
        (r"(\d+)\s*(秒|s|sec)\s*后", 1),
        (r"(\d+)\s*(分钟|min)\s*后", 60),
        (r"(\d+)\s*(小时|h|hr)\s*后", 3600),
    ]
    for pattern, multiplier in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return int(m.group(1)) * multiplier
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 持久化
# ═══════════════════════════════════════════════════════════════════════════════

def load_reminders() -> ReminderData:
    """加载提醒数据。"""
    if not REMINDERS_PATH.exists():
        return {"birthdays": [], "events": [], "last_reminded": {}}
    try:
        return json.loads(REMINDERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"birthdays": [], "events": [], "last_reminded": {}}


def save_reminders(data: ReminderData) -> None:
    """保存提醒数据。"""
    REMINDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REMINDERS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 事件提取
# ═══════════════════════════════════════════════════════════════════════════════

def extract_events_from_text(user_line: str) -> list[ReminderEntry]:
    """
    从用户输入中提取生日和事件。

    Args:
        user_line: 用户输入文本

    Returns:
        提取的事件列表
    """
    text = (user_line or "").strip()
    if not text:
        return []

    out: list[ReminderEntry] = []

    # 生日检测
    if "生日" in text:
        bday_date = None
        m = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", text)
        if m:
            bday_date = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        else:
            rel = _relative_date(text)
            if rel:
                bday_date = rel
        if bday_date:
            out.append({
                "type": "birthday",
                "description": "生日",
                "date": bday_date,
                "time": None,
            })

    # 事件检测
    delay_seconds = _parse_delay(text)
    event_time = _parse_time(text)
    event_date = _normalize_date(_parse_date(text), event_time)

    if delay_seconds is not None:
        target = _now_dt() + timedelta(seconds=delay_seconds)
        event_date = target.strftime("%Y-%m-%d")
        event_time = target.strftime("%H:%M:%S")

    has_keyword = any(k in text for k in ("提醒", "记得", "闹钟", "到点", "安排", "日程"))
    if has_keyword and (event_date or event_time):
        out.append({
            "type": "event",
            "description": _guess_description(text),
            "date": event_date or _now_dt().strftime("%Y-%m-%d"),
            "time": event_time,
        })

    return out


# ═══════════════════════════════════════════════════════════════════════════════
# 提醒查询
# ═══════════════════════════════════════════════════════════════════════════════

def _is_due(
    dt: datetime,
    reminded_key: str,
    last_reminded: dict[str, float],
) -> bool:
    """判断是否到达提醒时间窗口。"""
    from config import REMINDER_AHEAD_SECONDS
    now = _now_dt()
    due_window = now + timedelta(seconds=REMINDER_AHEAD_SECONDS)
    if not (now <= dt <= due_window):
        return False
    last_ts = last_reminded.get(reminded_key, 0.0)
    return (now.timestamp() - last_ts) > REMINDER_AHEAD_SECONDS


def check_due_reminders() -> tuple[list[BirthdayTuple], list[EventTuple]]:
    """
    检查到期提醒。

    Returns:
        (待祝福生日列表, 待提醒事件列表)
    """
    birthdays_greet: list[BirthdayTuple] = []
    events_remind: list[EventTuple] = []
    reminders = load_reminders()
    last_reminded: dict[str, float] = reminders.get("last_reminded", {})
    now = _now_dt()

    # 检查生日
    for bday in reminders.get("birthdays", []):
        desc = (bday.get("description") or "生日").strip()
        date_str = bday.get("date", "")
        time_str = bday.get("time")
        fallback_year = bday.get("year")
        dt = _parse_dt(date_str, time_str, fallback_year=fallback_year)
        if dt is None:
            continue
        next_dt = _next_occurrence(dt)
        key = f"bday:{date_str}"
        if _is_due(next_dt, key, last_reminded):
            birthdays_greet.append((desc, date_str, desc))

    # 检查事件
    for evt in reminders.get("events", []):
        desc = (evt.get("description") or "日程").strip()
        date_str = evt.get("date", "")
        time_str: str | None = evt.get("time")
        dt = _parse_dt(date_str, time_str)
        if dt is None:
            continue
        key = f"evt:{date_str}:{time_str or '00:00'}"

        if _is_due(dt, key, last_reminded):
            events_remind.append((desc, date_str, time_str, desc))
            continue

        # 补提醒：刚过点不久的事件
        added_ts = float(evt.get("added_ts") or 0.0)
        never_reminded = last_reminded.get(key, 0.0) <= 0.0
        is_overdue = dt <= now
        is_recently_added = added_ts > 0 and (now.timestamp() - added_ts) <= 24 * 3600
        overdue_seconds = (now - dt).total_seconds()
        is_slightly_overdue = 0 <= overdue_seconds <= 6 * 3600

        if never_reminded and is_overdue and is_recently_added and is_slightly_overdue:
            events_remind.append((desc, date_str, time_str, desc))

    return birthdays_greet, events_remind


def mark_reminded(keys: list[str]) -> None:
    """标记提醒已发送。"""
    reminders = load_reminders()
    now_ts = _now_dt().timestamp()
    last = reminders.setdefault("last_reminded", {})
    for k in keys:
        last[k] = now_ts
    save_reminders(reminders)


# ═══════════════════════════════════════════════════════════════════════════════
# 漏掉提醒检查（启动时关心）
# ═══════════════════════════════════════════════════════════════════════════════

def check_missed_reminders() -> tuple[list[tuple[str, str]], list[tuple[str, str, str | None]]]:
    """
    检查今日漏掉的生日或事件。

    Returns:
        (missed_birthdays, missed_events)
    """
    birthdays_greet: list[tuple[str, str]] = []
    events_remind: list[tuple[str, str, str | None]] = []
    reminders = load_reminders()
    last_reminded: dict[str, float] = reminders.get("last_reminded", {})
    now = _now_dt()

    # 检查今日生日
    for bday in reminders.get("birthdays", []):
        desc = (bday.get("description") or "生日").strip()
        date_str = bday.get("date", "")
        key = f"bday:{date_str}"
        if bday.get("date", "").startswith(f"{now.month:02d}-{now.day:02d}"):
            last_ts = last_reminded.get(key, 0.0)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            if last_ts < today_start:
                birthdays_greet.append((desc, date_str))

    # 检查今日事件
    today_str = now.strftime("%Y-%m-%d")
    for evt in reminders.get("events", []):
        desc = (evt.get("description") or "日程").strip()
        date_str = evt.get("date", "")
        time_str: str | None = evt.get("time")
        key = f"evt:{date_str}:{time_str or '00:00'}"

        if date_str != today_str:
            continue

        last_ts = last_reminded.get(key, 0.0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        if last_ts < today_start:
            events_remind.append((desc, date_str, time_str))

    return birthdays_greet, events_remind


# ═══════════════════════════════════════════════════════════════════════════════
# 添加记录
# ═══════════════════════════════════════════════════════════════════════════════

def add_birthday(date_str: str, description: str, year: int | None = None) -> None:
    """添加生日记录（自动去重）。"""
    reminders = load_reminders()
    for b in reminders["birthdays"]:
        if b.get("date") == date_str and b.get("description") == description:
            return
    entry: ReminderEntry = {
        "type": "birthday",
        "date": date_str,
        "description": description,
        "added_ts": _now_dt().timestamp(),
    }
    if year:
        entry["year"] = year
    reminders["birthdays"].append(entry)
    save_reminders(reminders)
    info(f"Added birthday: {description} ({date_str})")


def add_event(date_str: str, time_str: str | None, description: str) -> None:
    """添加事件记录（自动去重）。"""
    reminders = load_reminders()
    for e in reminders["events"]:
        if (
            e.get("date") == date_str
            and e.get("time") == time_str
            and e.get("description") == description
        ):
            return
    entry: ReminderEntry = {
        "type": "event",
        "date": date_str,
        "time": time_str,
        "description": description,
        "added_ts": _now_dt().timestamp(),
    }
    reminders["events"].append(entry)
    save_reminders(reminders)
    time_note = f" {time_str}" if time_str else ""
    info(f"Added event: {description} ({date_str}{time_note})")


# ═══════════════════════════════════════════════════════════════════════════════
# 祝福/提醒语生成
# ═══════════════════════════════════════════════════════════════════════════════

def generate_birthday_greeting(description: str) -> str | None:
    """生成生日祝福语。"""
    return f"生日快乐，{description}！愿你今天开心顺利。"


def generate_event_reminder(
    description: str,
    date_str: str,
    time_str: str | None = None,
) -> str | None:
    """生成事件提醒语（闺蜜风格）。"""
    if time_str:
        return f"好呀，{time_str} 记得 {description} 哦～"
    return f"好呀，{date_str} 提醒你 {description}，别忘了哦～"


def generate_caring_message(
    birthdays: list[tuple[str, str]],
    events: list[tuple[str, str, str | None]],
) -> str | None:
    """根据漏掉的提醒生成关心的问候语。"""
    if not birthdays and not events:
        return None

    from call_model import deepseek_chat
    from config import CHAT_SESSION_SYSTEM

    parts = []
    for desc, _ in birthdays:
        parts.append(f"今天是{desc}的生日")
    for desc, date_str, time_str in events:
        time_note = f"（{time_str}）" if time_str else ""
        parts.append(f"今天有「{desc}」的日程{time_note}")

    context = "、".join(parts)

    prompt = f"""你是用户的好闺蜜。今天是重要的一天，请用关心的语气问候她。

已知信息：
- {context}

请用自然的闺蜜口吻关心她，比如问今天过得怎么样、有没有被祝福等。
只输出这一句问候，不要前缀说明。"""

    reply = deepseek_chat(
        [
            {"role": "system", "content": CHAT_SESSION_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        thinking=False,
    )
    return reply.strip() if reply else None
