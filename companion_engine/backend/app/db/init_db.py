"""数据库初始化文件，负责创建 Companion Engine 的 SQLite 基础表。"""

from app.db.connection import get_connection


def init_db(db_path: str = "../data/companion.db") -> None:
    """初始化 SQLite 数据库表结构。"""
    conn = get_connection(db_path)

    try:
        # 使用 IF NOT EXISTS 保证初始化过程可重复执行。
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                preferred_address TEXT,
                preferred_support_style TEXT,
                initiative_tolerance TEXT,
                disliked_responses TEXT,
                liked_topics TEXT,
                avoided_topics TEXT,
                last_known_mood TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS persona_state (
                user_id TEXT PRIMARY KEY,
                role_style TEXT,
                warmth_level TEXT,
                initiative_level TEXT,
                analysis_level TEXT,
                playfulness_level TEXT,
                speech_length TEXT,
                companionship_style TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS persona_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                dimension TEXT,
                value TEXT,
                confidence REAL,
                evidence TEXT,
                source_type TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS relationship_state (
                user_id TEXT PRIMARY KEY,
                relationship_stage TEXT,
                trust_level REAL,
                intimacy_level REAL,
                user_openness REAL,
                recent_interaction_quality TEXT,
                last_meaningful_topic TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS long_term_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                memory_type TEXT,
                content TEXT,
                importance REAL,
                emotional_valence TEXT,
                source_text TEXT,
                created_at TEXT,
                last_used_at TEXT
            );

            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                intent TEXT,
                emotion TEXT,
                risk_level TEXT,
                strategy TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS short_term_dialogue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                strategy TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS emotion_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                emotion TEXT,
                risk_level TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS proactive_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                event_type TEXT,
                should_speak INTEGER,
                proactive_type TEXT,
                question_type TEXT,
                reason TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS interaction_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                robot_response TEXT,
                user_reaction TEXT,
                quality_score REAL,
                feedback_type TEXT,
                created_at TEXT
            );
            """
        )

        # 提交建表事务，确保数据库文件落盘后即可被后续模块使用。
        conn.commit()
    finally:
        conn.close()
