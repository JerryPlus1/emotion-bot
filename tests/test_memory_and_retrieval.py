from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from emotion_bot.chat import ChatRequest, ChatService
from emotion_bot.config import AppSettings
from emotion_bot.llm import MockLLM
from emotion_bot.memory import MemoryManager, extract_memory_candidates
from emotion_bot.proactive import ProactiveEngine
from emotion_bot.storage import MemoryStore


class MemoryExtractionTests(unittest.TestCase):
    def test_extracts_preferences_and_goals(self) -> None:
        candidates = extract_memory_candidates("我叫小李，我喜欢晚上写代码，我计划练习英语口语。")
        contents = [candidate.content for candidate in candidates]

        self.assertTrue(any("用户提到自己的身份" in content for content in contents))
        self.assertTrue(any("用户喜欢" in content for content in contents))
        self.assertTrue(any("用户的目标或计划" in content for content in contents))


class StoreRetrievalTests(unittest.TestCase):
    def test_memory_search_is_user_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "memory.sqlite3")
            store.upsert_memory("alice", "preference", "用户喜欢：晚上写代码", weight=1.2)
            store.upsert_memory("bob", "preference", "用户喜欢：清晨跑步", weight=1.2)

            alice_results = store.search_memories("alice", "写代码", limit=3)
            bob_results = store.search_memories("bob", "写代码", limit=3)

            self.assertEqual(alice_results[0].content, "用户喜欢：晚上写代码")
            self.assertEqual(bob_results, [])

    def test_profile_summary_updates_from_memories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "memory.sqlite3")
            manager = MemoryManager(store)
            message_id = store.add_message("alice", "user", "我喜欢咖啡，我打算学习钢琴。")

            manager.remember_from_user_message("alice", "我喜欢咖啡，我打算学习钢琴。", message_id)
            summary = store.get_profile_summary("alice")

            self.assertIn("偏好", summary)
            self.assertIn("目标与计划", summary)


class ProactiveTests(unittest.TestCase):
    def test_time_trigger_can_use_memory_topic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "memory.sqlite3")
            store.upsert_memory("alice", "goal", "用户的目标或计划：练习英语口语", weight=1.2)
            engine = ProactiveEngine(store)

            suggestion = engine.check(
                "alice",
                now=datetime(2026, 5, 7, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
                persist=False,
            )

            self.assertTrue(suggestion.active)
            self.assertEqual(suggestion.trigger, "morning")
            self.assertIn("英语", suggestion.topic)


class ChatServiceTests(unittest.TestCase):
    def test_current_message_is_not_retrieved_as_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "memory.sqlite3"
            store = MemoryStore(db_path)
            manager = MemoryManager(store)
            proactive = ProactiveEngine(store)
            settings = AppSettings(db_path=db_path, llm_backend="mock")
            service = ChatService(settings, store, manager, MockLLM(), proactive)

            first = service.chat(ChatRequest(user_id="alice", message="我喜欢晚上写代码。"))
            second = service.chat(ChatRequest(user_id="alice", message="你还记得我喜欢什么时候写代码吗？"))

            self.assertFalse(first.used_memory)
            self.assertTrue(second.used_memory)
            self.assertTrue(any(item.type == "memory" for item in second.used_contexts))


if __name__ == "__main__":
    unittest.main()
