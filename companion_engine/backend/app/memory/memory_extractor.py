"""记忆抽取文件，用简单规则从用户文本中抽取画像更新。"""

from app.schemas.memory import MemoryUpdate


def extract_memory_updates(user_text: str | None) -> list[MemoryUpdate]:
    """根据固定关键词抽取用户画像记忆更新。"""
    if not user_text:
        return []

    updates: list[MemoryUpdate] = []

    if "别分析" in user_text or "不要分析" in user_text:
        updates.append(
            MemoryUpdate(
                key="disliked_responses",
                value="过早分析",
                confidence=0.85,
                source_text=user_text,
            )
        )

    if "我喜欢你安静陪我" in user_text:
        updates.append(
            MemoryUpdate(
                key="preferred_support_style",
                value="quiet_company",
                confidence=0.9,
                source_text=user_text,
            )
        )

    if "我喜欢被安慰" in user_text:
        updates.append(
            MemoryUpdate(
                key="preferred_support_style",
                value="comfort_first",
                confidence=0.9,
                source_text=user_text,
            )
        )

    return updates
