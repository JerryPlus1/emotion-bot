"""人格更新抽取文件，用简单规则从用户反馈中抽取 Persona 更新。"""

from app.schemas.persona import PersonaUpdate


def extract_persona_updates(user_text: str | None) -> list[PersonaUpdate]:
    """根据固定关键词抽取 Persona 更新。"""
    if not user_text:
        return []

    updates: list[PersonaUpdate] = []

    if "温柔一点" in user_text:
        updates.append(
            PersonaUpdate(
                dimension="warmth_level",
                value="high",
                confidence=0.85,
                evidence=user_text,
                source_type="explicit_feedback",
            )
        )

    if "别那么理性" in user_text or "少分析" in user_text:
        updates.append(
            PersonaUpdate(
                dimension="analysis_level",
                value="low",
                confidence=0.85,
                evidence=user_text,
                source_type="explicit_feedback",
            )
        )

    if "活泼一点" in user_text:
        updates.append(
            PersonaUpdate(
                dimension="playfulness_level",
                value="high",
                confidence=0.8,
                evidence=user_text,
                source_type="explicit_feedback",
            )
        )

    return updates
