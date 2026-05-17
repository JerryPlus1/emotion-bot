"""用户画像存储文件，负责读取、保存和合并用户画像。"""

import json
from datetime import UTC, datetime
from typing import Any

from app.db.connection import get_connection
from app.schemas.memory import MemoryUpdate, UserProfile

LIST_FIELDS = {"disliked_responses", "liked_topics", "avoided_topics"}
TEXT_FIELDS = {
    "preferred_address",
    "preferred_support_style",
    "initiative_tolerance",
    "last_known_mood",
}


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于记录画像更新时间。"""
    return datetime.now(UTC).isoformat()


def _parse_json_list(raw_value: str | None) -> list[str]:
    """解析数据库里的 JSON 列表，损坏或类型不对时返回空列表。"""
    if not raw_value:
        return []

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    # 只保留字符串项，避免损坏数据影响后续画像合并逻辑。
    return [item for item in parsed if isinstance(item, str)]


def _dump_json_list(values: list[str]) -> str:
    """把字符串列表序列化为 JSON，保留中文内容。"""
    return json.dumps(values, ensure_ascii=False)


def _to_string_list(value: str | list[str]) -> list[str]:
    """把 MemoryUpdate 的值统一转为字符串列表，便于列表字段追加。"""
    if isinstance(value, str):
        return [value]

    return [item for item in value if isinstance(item, str)]


def _append_unique(existing_values: list[str], new_values: list[str]) -> list[str]:
    """按原有顺序追加新值，并自动去重。"""
    merged = list(existing_values)

    for value in new_values:
        if value not in merged:
            merged.append(value)

    return merged


def _profile_from_row(row: Any) -> UserProfile:
    """把 SQLite 查询结果转换为 UserProfile。"""
    return UserProfile(
        user_id=row["user_id"],
        preferred_address=row["preferred_address"],
        preferred_support_style=row["preferred_support_style"] or "unknown",
        initiative_tolerance=row["initiative_tolerance"] or "medium",
        disliked_responses=_parse_json_list(row["disliked_responses"]),
        liked_topics=_parse_json_list(row["liked_topics"]),
        avoided_topics=_parse_json_list(row["avoided_topics"]),
        last_known_mood=row["last_known_mood"],
    )


def get_profile(user_id: str, db_path: str) -> UserProfile:
    """读取用户画像；如果数据库中不存在记录，则返回默认画像。"""
    conn = get_connection(db_path)

    try:
        row = conn.execute(
            """
            SELECT
                user_id,
                preferred_address,
                preferred_support_style,
                initiative_tolerance,
                disliked_responses,
                liked_topics,
                avoided_topics,
                last_known_mood
            FROM user_profile
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # 没有记录时返回 Schema 自带默认值，保持首次使用体验简单。
        return UserProfile(user_id=user_id)

    return _profile_from_row(row)


def save_profile(profile: UserProfile, db_path: str) -> None:
    """保存用户画像；如果用户已存在，则覆盖更新。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO user_profile (
                user_id,
                preferred_address,
                preferred_support_style,
                initiative_tolerance,
                disliked_responses,
                liked_topics,
                avoided_topics,
                last_known_mood,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_address = excluded.preferred_address,
                preferred_support_style = excluded.preferred_support_style,
                initiative_tolerance = excluded.initiative_tolerance,
                disliked_responses = excluded.disliked_responses,
                liked_topics = excluded.liked_topics,
                avoided_topics = excluded.avoided_topics,
                last_known_mood = excluded.last_known_mood,
                updated_at = excluded.updated_at
            """,
            (
                profile.user_id,
                profile.preferred_address,
                profile.preferred_support_style,
                profile.initiative_tolerance,
                _dump_json_list(profile.disliked_responses),
                _dump_json_list(profile.liked_topics),
                _dump_json_list(profile.avoided_topics),
                profile.last_known_mood,
                _now_iso(),
            ),
        )

        # 提交画像保存事务，确保后续读取能拿到最新状态。
        conn.commit()
    finally:
        conn.close()


def apply_memory_updates(
    user_id: str,
    updates: list[MemoryUpdate],
    db_path: str,
) -> UserProfile:
    """把高可信度记忆更新合并到用户画像，并返回更新后的画像。"""
    profile = get_profile(user_id, db_path)

    for update in updates:
        # 只应用可信度足够高的更新，低可信度信息暂时忽略。
        if update.confidence < 0.7:
            continue

        if update.key in LIST_FIELDS:
            current_values = getattr(profile, update.key)
            new_values = _to_string_list(update.value)
            setattr(profile, update.key, _append_unique(current_values, new_values))
            continue

        if update.key in TEXT_FIELDS:
            # 普通字段直接覆盖；列表值只取第一个字符串，避免写入奇怪结构。
            new_values = _to_string_list(update.value)
            if new_values:
                setattr(profile, update.key, new_values[0])

    save_profile(profile, db_path)
    return profile
