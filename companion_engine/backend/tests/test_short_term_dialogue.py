"""短期对话记忆和重复控制测试。"""

from pathlib import Path

from app.core.engine import handle_event
from app.db.init_db import init_db
from app.humanlike.repetition_guard import avoid_repetitive_reply
from app.memory.short_term_dialogue_store import (
    add_dialogue_turn,
    clear_short_term_dialogue,
    get_recent_bot_messages,
    get_recent_dialogue,
)
from app.schemas.engine import EngineInput, SceneContext


def _db_path(tmp_path: Path) -> str:
    """返回测试用临时数据库路径，避免污染真实 data 目录。"""
    return str(tmp_path / "companion.db")


def test_similar_reply_is_rewritten() -> None:
    """测试连续相似回复会被改写或缩短。"""
    reply = avoid_repetitive_reply(
        "我在这儿陪你。",
        ["我在这儿陪你。"],
    )

    assert reply != "我在这儿陪你。"
    assert "我在这儿陪你" not in reply


def test_recent_bot_messages_can_be_read(tmp_path: Path) -> None:
    """测试可以读取最近机器人消息。"""
    db_path = _db_path(tmp_path)
    init_db(db_path)
    add_dialogue_turn("user_a", "user", "你好", None, db_path)
    add_dialogue_turn("user_a", "assistant", "我在。", "quiet_company", db_path)
    add_dialogue_turn("user_a", "assistant", "慢慢来。", "quiet_company", db_path)

    messages = get_recent_bot_messages("user_a", 2, db_path)

    assert messages == ["我在。", "慢慢来。"]


def test_clear_short_term_dialogue_makes_recent_empty(tmp_path: Path) -> None:
    """测试清空短期对话后读取为空。"""
    db_path = _db_path(tmp_path)
    init_db(db_path)
    add_dialogue_turn("user_a", "assistant", "我在。", "quiet_company", db_path)

    clear_short_term_dialogue("user_a", db_path)

    assert get_recent_dialogue("user_a", 5, db_path) == []


def test_engine_writes_short_term_dialogue(tmp_path: Path) -> None:
    """测试 engine 会写入用户和机器人短期对话。"""
    db_path = _db_path(tmp_path)

    handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="你好",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        db_path,
    )
    dialogue = get_recent_dialogue("default_user", 10, db_path)

    assert [turn["role"] for turn in dialogue] == ["user", "assistant"]
    assert dialogue[0]["content"] == "你好"
