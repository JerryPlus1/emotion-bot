"""用户画像存储测试，验证读取、保存和记忆更新合并逻辑。"""

from pathlib import Path

from app.db.connection import get_connection
from app.db.init_db import init_db
from app.memory.profile_store import apply_memory_updates, get_profile, save_profile
from app.schemas.memory import MemoryUpdate, UserProfile


def _temp_db(tmp_path: Path) -> str:
    """创建临时数据库并返回路径，避免污染真实 data 目录。"""
    db_path = tmp_path / "companion.db"
    init_db(str(db_path))
    return str(db_path)


def test_get_profile_returns_default_profile_first_time(tmp_path: Path) -> None:
    """测试首次读取不存在的用户时返回默认画像。"""
    db_path = _temp_db(tmp_path)

    profile = get_profile("user_a", db_path)

    assert profile.user_id == "user_a"
    assert profile.preferred_support_style == "unknown"
    assert profile.initiative_tolerance == "medium"
    assert profile.disliked_responses == []
    assert profile.liked_topics == []
    assert profile.avoided_topics == []
    assert profile.last_known_mood is None


def test_save_profile_can_be_read_back(tmp_path: Path) -> None:
    """测试保存后的用户画像可以完整读回。"""
    db_path = _temp_db(tmp_path)
    profile = UserProfile(
        user_id="user_a",
        preferred_address="小夏",
        preferred_support_style="listen_first",
        initiative_tolerance="low",
        disliked_responses=["说教"],
        liked_topics=["音乐"],
        avoided_topics=["考试"],
        last_known_mood="tired",
    )

    save_profile(profile, db_path)
    saved_profile = get_profile("user_a", db_path)

    assert saved_profile == profile


def test_apply_memory_updates_updates_text_fields(tmp_path: Path) -> None:
    """测试记忆更新可以覆盖普通文本字段。"""
    db_path = _temp_db(tmp_path)
    updates = [
        MemoryUpdate(
            key="preferred_address",
            value="阿夏",
            confidence=0.8,
            source_text="以后叫我阿夏吧。",
        ),
        MemoryUpdate(
            key="last_known_mood",
            value="happy",
            confidence=0.9,
            source_text="今天还挺开心的。",
        ),
    ]

    profile = apply_memory_updates("user_a", updates, db_path)

    assert profile.preferred_address == "阿夏"
    assert profile.last_known_mood == "happy"


def test_apply_memory_updates_updates_list_fields_with_dedup(tmp_path: Path) -> None:
    """测试列表字段会追加并去重。"""
    db_path = _temp_db(tmp_path)
    save_profile(UserProfile(user_id="user_a", liked_topics=["音乐"]), db_path)
    updates = [
        MemoryUpdate(
            key="liked_topics",
            value=["音乐", "散步", "电影"],
            confidence=0.95,
            source_text="我喜欢音乐、散步和电影。",
        ),
        MemoryUpdate(
            key="avoided_topics",
            value="加班",
            confidence=0.8,
            source_text="别总和我聊加班。",
        ),
    ]

    profile = apply_memory_updates("user_a", updates, db_path)

    assert profile.liked_topics == ["音乐", "散步", "电影"]
    assert profile.avoided_topics == ["加班"]


def test_low_confidence_update_is_ignored(tmp_path: Path) -> None:
    """测试低可信度更新不会写入用户画像。"""
    db_path = _temp_db(tmp_path)
    updates = [
        MemoryUpdate(
            key="preferred_support_style",
            value="give_advice",
            confidence=0.6,
            source_text="也许你可以给建议。",
        )
    ]

    profile = apply_memory_updates("user_a", updates, db_path)

    assert profile.preferred_support_style == "unknown"


def test_unknown_key_does_not_crash(tmp_path: Path) -> None:
    """测试未知 key 会被忽略，不会导致合并流程崩溃。"""
    db_path = _temp_db(tmp_path)
    updates = [
        MemoryUpdate(
            key="unknown_field",
            value="some value",
            confidence=0.9,
            source_text="未知字段测试。",
        )
    ]

    profile = apply_memory_updates("user_a", updates, db_path)

    assert profile == UserProfile(user_id="user_a")


def test_broken_json_list_falls_back_to_empty_list(tmp_path: Path) -> None:
    """测试数据库中的损坏 JSON 列表会容错为空列表。"""
    db_path = _temp_db(tmp_path)
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO user_profile (
                user_id,
                preferred_support_style,
                initiative_tolerance,
                disliked_responses,
                liked_topics,
                avoided_topics
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("user_a", "unknown", "medium", "not-json", "[1, 2]", "[]"),
        )
        conn.commit()
    finally:
        conn.close()

    profile = get_profile("user_a", db_path)

    assert profile.disliked_responses == []
    assert profile.liked_topics == []
