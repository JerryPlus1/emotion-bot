"""Proactive conversation triggers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .storage import MemoryStore


@dataclass
class ProactiveSuggestion:
    active: bool
    trigger: str
    topic: str
    message: str
    context: list[dict] = field(default_factory=list)


class ProactiveEngine:
    def __init__(self, store: MemoryStore, local_timezone: str = "Asia/Shanghai"):
        self.store = store
        self.local_timezone = local_timezone

    def check(
        self,
        user_id: str,
        scenario: str | None = None,
        now: datetime | None = None,
        persist: bool = True,
    ) -> ProactiveSuggestion:
        self.store.ensure_user(user_id)
        now = now or datetime.now(ZoneInfo(self.local_timezone))
        if now.tzinfo is None:
            now = now.replace(tzinfo=ZoneInfo(self.local_timezone))

        trigger = self._time_trigger(now)
        scenario_trigger = self._scenario_trigger(scenario or "")
        inactivity_trigger = self._inactivity_trigger(user_id, now)

        chosen = scenario_trigger or trigger or inactivity_trigger
        if not chosen:
            return ProactiveSuggestion(False, "", "", "")

        if self._recently_sent(user_id, chosen, now):
            return ProactiveSuggestion(False, "", "", "")

        topic, context = self._topic_from_memory(user_id, chosen)
        message = self._message_for_trigger(chosen, topic)
        suggestion = ProactiveSuggestion(True, chosen, topic, message, context)
        if persist:
            self.store.add_proactive_event(user_id, chosen, message, {"topic": topic, "scenario": scenario})
        return suggestion

    def _time_trigger(self, now: datetime) -> str:
        hour = now.hour
        if 7 <= hour <= 9:
            return "morning"
        if 12 <= hour <= 13:
            return "noon"
        if 18 <= hour <= 21:
            return "evening"
        if 22 <= hour or hour <= 1:
            return "late_night"
        return ""

    def _scenario_trigger(self, scenario: str) -> str:
        normalized = scenario.strip().lower()
        if not normalized:
            return ""
        mapping = {
            "工作": "work_focus",
            "学习": "study_focus",
            "压力": "stress",
            "低落": "stress",
            "睡前": "late_night",
            "久坐": "break",
            "运动": "health",
            "饭点": "meal",
        }
        for keyword, trigger in mapping.items():
            if keyword in normalized:
                return trigger
        return "scene"

    def _inactivity_trigger(self, user_id: str, now: datetime) -> str:
        messages = self.store.recent_messages(user_id, limit=1)
        if not messages:
            return "welcome"
        last = messages[-1]
        created = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        elapsed = now.astimezone(timezone.utc) - created.astimezone(timezone.utc)
        if elapsed >= timedelta(hours=8):
            return "inactivity"
        return ""

    def _recently_sent(self, user_id: str, trigger: str, now: datetime) -> bool:
        events = self.store.recent_proactive_events(user_id, limit=12)
        cooldown = timedelta(hours=6)
        if trigger in {"morning", "noon", "evening", "late_night"}:
            cooldown = timedelta(hours=18)
        for event in events:
            if event["kind"] != trigger:
                continue
            created = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if now.astimezone(timezone.utc) - created.astimezone(timezone.utc) < cooldown:
                return True
        return False

    def _topic_from_memory(self, user_id: str, trigger: str) -> tuple[str, list[dict]]:
        query_by_trigger = {
            "morning": "计划 目标 今天 工作 学习",
            "noon": "午饭 休息 工作 学习 压力",
            "evening": "今天 最近 喜欢 计划 放松",
            "late_night": "睡眠 压力 情绪 明天",
            "work_focus": "工作 任务 计划 压力",
            "study_focus": "学习 计划 目标",
            "stress": "压力 担心 情绪 低落",
            "break": "休息 久坐 健康",
            "health": "运动 健康 习惯",
            "meal": "吃饭 喜欢 午饭 晚饭",
            "inactivity": "最近 计划 喜欢 目标",
            "scene": "最近 计划 喜欢",
            "welcome": "欢迎 开始",
        }
        query = query_by_trigger.get(trigger, "最近")
        memories = self.store.search_memories(user_id, query, limit=3)
        context = [
            {
                "type": item.type,
                "content": item.content,
                "score": round(item.score, 3),
                "metadata": item.metadata,
            }
            for item in memories
        ]
        if memories:
            return memories[0].content, context
        fallback = {
            "morning": "今天想怎样开始",
            "noon": "要不要短暂休息一下",
            "evening": "今天过得怎么样",
            "late_night": "睡前放松一下",
            "welcome": "第一次聊天",
        }
        return fallback.get(trigger, "聊聊现在的状态"), context

    def _message_for_trigger(self, trigger: str, topic: str) -> str:
        templates = {
            "morning": "早上好。想到你之前提到的「{topic}」，今天要不要先定一个很小的开始？",
            "noon": "到中午了。可以暂停一下，我也想听听你上午和「{topic}」有关的进展。",
            "evening": "晚上好。今天差不多收束了，要不要聊聊「{topic}」现在变成了什么样？",
            "late_night": "已经很晚了。我们可以轻一点聊，围绕「{topic}」做个睡前整理。",
            "work_focus": "你现在像是在工作场景里。我可以陪你把「{topic}」拆成下一步。",
            "study_focus": "学习模式启动。我想起「{topic}」，要不要一起排个短计划？",
            "stress": "我注意到这个场景可能有压力。可以从「{topic}」开始，慢慢说。",
            "break": "该活动一下了。先离开屏幕一分钟，再回来聊「{topic}」。",
            "health": "我们可以聊聊身体状态，也可以把「{topic}」放进今天的小习惯里。",
            "meal": "饭点到了。吃点东西也算照顾自己，顺便可以聊聊「{topic}」。",
            "inactivity": "有一阵没聊了。我还记得「{topic}」，想听听后来怎么样了。",
            "scene": "我检测到新的场景。要不要从「{topic}」开始聊？",
            "welcome": "欢迎回来。我们可以从今天的心情开始，也可以告诉我你希望我记住什么。",
        }
        return templates.get(trigger, "要不要聊聊「{topic}」？").format(topic=topic)
