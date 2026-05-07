"""Long-term memory extraction and profile summarization."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .storage import MemoryStore


@dataclass
class MemoryCandidate:
    kind: str
    content: str
    weight: float


class MemoryManager:
    def __init__(self, store: MemoryStore):
        self.store = store

    def remember_from_user_message(self, user_id: str, message: str, source_message_id: int) -> list[MemoryCandidate]:
        candidates = extract_memory_candidates(message)
        for candidate in candidates:
            self.store.upsert_memory(
                user_id=user_id,
                kind=candidate.kind,
                content=candidate.content,
                source_message_id=source_message_id,
                weight=candidate.weight,
            )
        if candidates:
            self.refresh_profile_summary(user_id)
        return candidates

    def refresh_profile_summary(self, user_id: str) -> str:
        memories = self.store.list_memories(user_id, limit=80)
        grouped: dict[str, list[str]] = {
            "identity": [],
            "preference": [],
            "goal": [],
            "relationship": [],
            "routine": [],
            "note": [],
        }
        for item in memories:
            kind = item["kind"] if item["kind"] in grouped else "note"
            content = item["content"].strip()
            if content and content not in grouped[kind]:
                grouped[kind].append(content)

        labels = {
            "identity": "身份与称呼",
            "preference": "偏好",
            "goal": "目标与计划",
            "relationship": "重要关系",
            "routine": "习惯与日程",
            "note": "近期关注",
        }

        lines: list[str] = []
        for kind, label in labels.items():
            values = grouped[kind][:8]
            if values:
                lines.append(f"{label}: " + "；".join(values))

        summary = "\n".join(lines)
        self.store.update_profile_summary(user_id, summary)
        return summary


def _clean_fragment(text: str, max_length: int = 80) -> str:
    text = re.sub(r"\s+", " ", text).strip(" ，。,.;；！!？?")
    return text[:max_length].strip()


def extract_memory_candidates(message: str) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []
    text = message.strip()
    if not text:
        return candidates

    patterns: list[tuple[str, str, float, str]] = [
        (r"(?:我叫|我的名字是|我是)([^，。！？\n]{1,24})", "identity", 1.4, "用户提到自己的身份/称呼：{}"),
        (r"(?:我是一个|我是一名|我的职业是|我在做)([^，。！？\n]{1,36})", "identity", 1.2, "用户的身份或职业：{}"),
        (r"(?:我来自|我住在|我现在在)([^，。！？\n]{1,36})", "identity", 1.1, "用户的位置相关信息：{}"),
        (r"(?:我喜欢|我爱|我偏爱|我比较喜欢)([^，。！？\n]{1,60})", "preference", 1.3, "用户喜欢：{}"),
        (r"(?:我不喜欢|我讨厌|我不太喜欢)([^，。！？\n]{1,60})", "preference", 1.3, "用户不喜欢：{}"),
        (r"(?:我想|我希望|我打算|我计划|我准备)([^，。！？\n]{1,70})", "goal", 1.1, "用户的目标或计划：{}"),
        (r"(?:我正在|我最近在|这段时间我在)([^，。！？\n]{1,70})", "goal", 1.0, "用户近期正在做：{}"),
        (r"(?:我每天|我通常|我习惯|我一般)([^，。！？\n]{1,70})", "routine", 1.0, "用户的习惯：{}"),
        (r"(?:我的朋友|我的家人|我妈妈|我爸爸|我对象|我女朋友|我男朋友)([^，。！？\n]{1,70})", "relationship", 1.0, "用户的重要关系：{}"),
        (r"(?:my name is|i am|i'm)\s+([^,.!?\n]{1,40})", "identity", 1.2, "用户用英文提到身份/称呼：{}"),
        (r"(?:i like|i love|i prefer)\s+([^,.!?\n]{1,60})", "preference", 1.2, "用户喜欢：{}"),
        (r"(?:i want to|i hope to|i plan to)\s+([^,.!?\n]{1,70})", "goal", 1.1, "用户的目标或计划：{}"),
    ]

    lowered = text.lower()
    for pattern, kind, weight, template in patterns:
        target = lowered if pattern.startswith("(?:my") or pattern.startswith("(?:i") else text
        for match in re.finditer(pattern, target, flags=re.IGNORECASE):
            fragment = _clean_fragment(match.group(1))
            if fragment:
                candidates.append(MemoryCandidate(kind=kind, content=template.format(fragment), weight=weight))

    if not candidates and len(text) >= 24 and re.search(r"\b我\b|我|我的|最近|以后|打算|喜欢|担心|压力", text):
        candidates.append(
            MemoryCandidate(kind="note", content=f"用户曾提到：{_clean_fragment(text, 120)}", weight=0.7)
        )

    deduped: list[MemoryCandidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate.kind, candidate.content)
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped
