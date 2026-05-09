"""SQLite persistence for chat history, memories and knowledge chunks."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .text_index import (
    cosine_similarity,
    deserialize_vector,
    keyword_overlap,
    serialize_vector,
    sparse_embedding,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SearchResult:
    id: int
    type: str
    content: str
    score: float
    weight: float
    created_at: str
    metadata: dict[str, Any]


class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init_db(self) -> None:
        with self._lock, self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    profile_summary TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    conversation_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS memory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_message_id INTEGER,
                    weight REAL NOT NULL DEFAULT 1.0,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, kind, content),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(source_message_id) REFERENCES messages(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    source TEXT,
                    content TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS proactive_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """
            )

    def ensure_user(self, user_id: str, display_name: str | None = None) -> None:
        now = utc_now()
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO users(user_id, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name = COALESCE(excluded.display_name, users.display_name),
                    updated_at = excluded.updated_at
                """,
                (user_id, display_name, now, now),
            )

    def list_users(self) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT user_id, display_name, profile_summary, created_at, updated_at
                FROM users
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def create_conversation(self, user_id: str, title: str | None = None) -> int:
        self.ensure_user(user_id)
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO conversations(user_id, title, created_at) VALUES (?, ?, ?)",
                (user_id, title, utc_now()),
            )
            return int(cursor.lastrowid)

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        conversation_id: int | None = None,
    ) -> int:
        self.ensure_user(user_id)
        embedding_json = serialize_vector(sparse_embedding(content))
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO messages(user_id, conversation_id, role, content, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, conversation_id, role, content, embedding_json, utc_now()),
            )
            connection.execute(
                "UPDATE users SET updated_at = ? WHERE user_id = ?",
                (utc_now(), user_id),
            )
            return int(cursor.lastrowid)

    def recent_messages(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, conversation_id, role, content, created_at
                FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def search_messages(self, user_id: str, query: str, limit: int = 6) -> list[SearchResult]:
        query_vector = sparse_embedding(query)
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, embedding_json, created_at
                FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 800
                """,
                (user_id,),
            ).fetchall()

        results: list[SearchResult] = []
        seen_contents: set[str] = set()
        for row in rows:
            content = f'{row["role"]}: {row["content"]}'
            if content in seen_contents:
                continue
            vector_score = cosine_similarity(query_vector, deserialize_vector(row["embedding_json"]))
            overlap_score = keyword_overlap(query, row["content"])
            if overlap_score <= 0:
                continue
            score = vector_score * 0.75 + overlap_score * 0.25
            seen_contents.add(content)
            results.append(
                SearchResult(
                    id=int(row["id"]),
                    type="history",
                    content=content,
                    score=score,
                    weight=1.0,
                    created_at=row["created_at"],
                    metadata={"role": row["role"]},
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def upsert_memory(
        self,
        user_id: str,
        kind: str,
        content: str,
        source_message_id: int | None = None,
        weight: float = 1.0,
    ) -> int:
        self.ensure_user(user_id)
        now = utc_now()
        embedding_json = serialize_vector(sparse_embedding(content))
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO memory_items(
                    user_id, kind, content, source_message_id, weight, embedding_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, kind, content) DO UPDATE SET
                    weight = max(memory_items.weight, excluded.weight),
                    source_message_id = COALESCE(excluded.source_message_id, memory_items.source_message_id),
                    embedding_json = excluded.embedding_json,
                    updated_at = excluded.updated_at
                """,
                (user_id, kind, content, source_message_id, weight, embedding_json, now, now),
            )
            row = connection.execute(
                "SELECT id FROM memory_items WHERE user_id = ? AND kind = ? AND content = ?",
                (user_id, kind, content),
            ).fetchone()
            return int(row["id"])

    def list_memories(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, kind, content, weight, created_at, updated_at
                FROM memory_items
                WHERE user_id = ?
                ORDER BY weight DESC, updated_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_memories(self, user_id: str, query: str, limit: int = 8) -> list[SearchResult]:
        query_vector = sparse_embedding(query)
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, kind, content, weight, embedding_json, created_at, updated_at
                FROM memory_items
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1000
                """,
                (user_id,),
            ).fetchall()

        results: list[SearchResult] = []
        for row in rows:
            vector_score = cosine_similarity(query_vector, deserialize_vector(row["embedding_json"]))
            overlap_score = keyword_overlap(query, row["content"])
            if overlap_score <= 0:
                continue
            base_score = vector_score * 0.75 + overlap_score * 0.25
            weight = float(row["weight"])
            results.append(
                SearchResult(
                    id=int(row["id"]),
                    type="memory",
                    content=row["content"],
                    score=base_score * weight,
                    weight=weight,
                    created_at=row["created_at"],
                    metadata={"kind": row["kind"], "updated_at": row["updated_at"]},
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def add_document(
        self,
        title: str,
        content: str,
        source: str | None = None,
        user_id: str | None = None,
        weight: float = 1.0,
    ) -> int:
        embedding_json = serialize_vector(sparse_embedding(content))
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO documents(user_id, title, source, content, weight, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, source, content, weight, embedding_json, utc_now()),
            )
            return int(cursor.lastrowid)

    def search_documents(
        self,
        query: str,
        user_id: str | None = None,
        limit: int = 6,
    ) -> list[SearchResult]:
        query_vector = sparse_embedding(query)
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, title, source, content, weight, embedding_json, created_at
                FROM documents
                WHERE user_id IS NULL OR user_id = ?
                ORDER BY id DESC
                LIMIT 1200
                """,
                (user_id,),
            ).fetchall()

        results: list[SearchResult] = []
        for row in rows:
            vector_score = cosine_similarity(query_vector, deserialize_vector(row["embedding_json"]))
            overlap_score = keyword_overlap(query, row["content"])
            if overlap_score <= 0:
                continue
            base_score = vector_score * 0.75 + overlap_score * 0.25
            weight = float(row["weight"])
            results.append(
                SearchResult(
                    id=int(row["id"]),
                    type="document",
                    content=row["content"],
                    score=base_score * weight,
                    weight=weight,
                    created_at=row["created_at"],
                    metadata={"title": row["title"], "source": row["source"], "user_id": row["user_id"]},
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def get_profile_summary(self, user_id: str) -> str:
        self.ensure_user(user_id)
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT profile_summary FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return "" if row is None else row["profile_summary"] or ""

    def update_profile_summary(self, user_id: str, summary: str) -> None:
        self.ensure_user(user_id)
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET profile_summary = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (summary, utc_now(), user_id),
            )

    def add_proactive_event(
        self,
        user_id: str,
        kind: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        self.ensure_user(user_id)
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO proactive_events(user_id, kind, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, kind, content, json.dumps(metadata or {}, ensure_ascii=False), utc_now()),
            )
            return int(cursor.lastrowid)

    def recent_proactive_events(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, kind, content, metadata_json, created_at
                FROM proactive_events
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            except json.JSONDecodeError:
                item["metadata"] = {}
            events.append(item)
        return events

    def delete_user_data(self, user_id: str) -> None:
        with self._lock, self._connection() as connection:
            connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
