"""数据库连接模块，负责创建 SQLite 连接并配置基础连接选项。"""

import sqlite3
from pathlib import Path


def get_connection(db_path: str = "../data/companion.db") -> sqlite3.Connection:
    """获取 SQLite 连接，并自动创建数据库文件所在目录。"""
    database_path = Path(db_path)

    # 首次运行时确保 data 目录存在，避免 SQLite 打开数据库文件失败。
    database_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path)

    # 让查询结果可以像字典一样按列名读取，方便后续 store 层使用。
    conn.row_factory = sqlite3.Row
    return conn
