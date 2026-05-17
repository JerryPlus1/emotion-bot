"""数据库初始化测试，确保 SQLite 基础表可以在临时路径中创建。"""

import sqlite3
from pathlib import Path

from app.db.connection import get_connection
from app.db.init_db import init_db


def test_init_db_creates_database_file(tmp_path: Path) -> None:
    """测试 init_db 会创建指定的临时数据库文件。"""
    db_path = tmp_path / "companion.db"

    init_db(str(db_path))

    assert db_path.is_file()


def test_init_db_creates_all_tables(tmp_path: Path) -> None:
    """测试 init_db 会创建第 2 阶段要求的所有数据表。"""
    db_path = tmp_path / "companion.db"
    expected_tables = {
        "user_profile",
        "persona_state",
        "persona_preferences",
        "relationship_state",
        "long_term_memories",
        "conversation_logs",
        "proactive_logs",
        "interaction_feedback",
    }

    init_db(str(db_path))

    conn = get_connection(str(db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    finally:
        conn.close()

    table_names = {row["name"] for row in rows}
    assert expected_tables.issubset(table_names)


def test_get_connection_row_factory_is_usable(tmp_path: Path) -> None:
    """测试 get_connection 返回的连接可以通过列名读取查询结果。"""
    db_path = tmp_path / "companion.db"

    conn = get_connection(str(db_path))
    try:
        assert conn.row_factory is sqlite3.Row

        conn.execute("CREATE TABLE sample (name TEXT)")
        conn.execute("INSERT INTO sample (name) VALUES (?)", ("companion",))
        row = conn.execute("SELECT name FROM sample").fetchone()
    finally:
        conn.close()

    assert row["name"] == "companion"
