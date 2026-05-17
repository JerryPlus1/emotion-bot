"""Prompt builder for the local GGUF model.

The backend keeps the complex state and gives the small local model only a
short expression task. This makes 2B-class GGUF models much more stable than
asking them to read the full profile, relationship state, memories, safety
rules, and JSON schema at once.
"""

from typing import Any


def _as_value(value: Any) -> Any:
    """Return Enum.value when available; otherwise return the original value."""
    return getattr(value, "value", value)


def _memory_content(memory: Any) -> str:
    if isinstance(memory, dict):
        return str(memory.get("content", "")).strip()
    return str(getattr(memory, "content", "")).strip()


def _relationship_boundary(relationship_state: Any) -> str:
    stage = str(getattr(relationship_state, "relationship_stage", "stranger"))
    if stage in {"trusted", "close_friend"}:
        return "关系分寸：比较熟，可以温暖一点，但不要制造依赖。"
    if stage == "familiar":
        return "关系分寸：有点熟悉，语气自然温和，不要过度亲密。"
    return "关系分寸：刚认识，礼貌温和，不要暧昧，不要过度亲密。"


def _profile_hint(user_profile: Any) -> str:
    hints: list[str] = []

    support_style = str(getattr(user_profile, "preferred_support_style", "unknown"))
    if support_style and support_style != "unknown":
        hints.append(f"用户偏好的支持方式：{support_style}。")

    disliked = list(getattr(user_profile, "disliked_responses", []) or [])
    if disliked:
        hints.append(f"避免这些回复方式：{', '.join(map(str, disliked[:2]))}。")

    if not hints:
        return "用户偏好：自然陪伴，少说教，少分析。"

    return " ".join(hints)


def _persona_hint(persona: Any) -> str:
    warmth = str(getattr(persona, "warmth_level", "medium"))
    analysis = str(getattr(persona, "analysis_level", "medium"))
    playfulness = str(getattr(persona, "playfulness_level", "medium"))
    length = str(getattr(persona, "speech_length", "medium"))
    return f"表达风格：温暖度 {warmth}，分析程度 {analysis}，玩笑程度 {playfulness}，长度 {length}。"


def _memory_hint(memories: list[Any]) -> str:
    for memory in memories[:2]:
        content = _memory_content(memory)
        if content:
            return f"可轻轻参考这条记忆：{content}。如果不相关，不要硬提。"
    return "本轮没有必须引用的记忆。"


def _strategy_goal(strategy: Any) -> str:
    strategy_value = str(_as_value(strategy))
    goals = {
        "quiet_company": "回复方向：轻轻陪伴，不追问。",
        "emotional_validation": "回复方向：先接住情绪，别急着讲道理。",
        "choice_offering": "回复方向：给一个很轻的选择，不要替用户做决定。",
        "soft_greeting": "回复方向：自然打招呼，简短一点。",
        "profile_question": "回复方向：如果要问，只问一个很轻的问题。",
        "persona_question": "回复方向：询问用户偏好的陪伴方式，但不要像问卷。",
        "playful_response": "回复方向：轻松一点，但不要抢用户情绪。",
        "memory_recall": "回复方向：可以轻轻提到相关记忆，但不要显得监控用户。",
        "crisis_redirect": "回复方向：安全优先，温和建议联系现实中可信任的人或当地紧急帮助。",
    }
    return goals.get(strategy_value, "回复方向：自然回应用户刚刚说的话。")


def _safety_hint(risk_level: Any) -> str:
    risk_value = str(_as_value(risk_level))
    if risk_value in {"high", "medium"}:
        return "安全要求：必须建议用户联系现实中可信任的人或当地紧急帮助，不要承诺替代专业帮助。"
    return "安全要求：不要鼓励伤害自己或他人，不要替代专业帮助。"


def build_prompt(
    user_text: str | None,
    context: Any,
    user_profile: Any,
    persona: Any,
    relationship_state: Any,
    memories: list[Any],
    intent: Any,
    emotion: Any,
    risk_level: Any,
    strategy: Any,
    emotion_trend: Any = "stable",
) -> str:
    """Build a short prompt where the model only writes the final reply text."""
    _ = context
    user_line = (user_text or "").strip() or "用户没有说话。"
    intent_value = str(_as_value(intent))
    emotion_value = str(_as_value(emotion))
    trend_value = str(_as_value(emotion_trend))

    task = "\n".join(
        [
            f"用户刚刚说：{user_line}",
            f"后端判断：意图 {intent_value}，情绪 {emotion_value}，情绪趋势 {trend_value}。",
            _profile_hint(user_profile),
            _relationship_boundary(relationship_state),
            _persona_hint(persona),
            _memory_hint(memories),
            _strategy_goal(strategy),
            _safety_hint(risk_level),
            "输出要求：只输出一句自然中文回复，不要 JSON，不要 Markdown，不要解释，不要写分析过程。",
        ]
    )

    return "\n".join(
        [
            "<|im_start|>system",
            "你是一个温柔、有分寸的中文陪伴者。后端已经完成画像、关系、记忆、风险和策略判断；你只负责把回复意图说成一句自然中文。",
            "<|im_end|>",
            "<|im_start|>user",
            task,
            "<|im_end|>",
            "<|im_start|>assistant",
        ]
    )
