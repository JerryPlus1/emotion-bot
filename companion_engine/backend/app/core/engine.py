"""对话引擎核心文件，串联第 12 阶段的完整 Mock 对话流程。"""

from datetime import UTC, datetime

from app.core.context_builder import build_context
from app.db.connection import get_connection
from app.db.init_db import init_db
from app.evaluation.feedback_store import save_interaction_feedback
from app.evaluation.response_evaluator import evaluate_user_reaction
from app.humanlike.humanlike_controller import make_reply_humanlike
from app.humanlike.memory_recall_policy import should_recall_memory
from app.humanlike.question_throttle import should_ask_question
from app.humanlike.silence_policy import should_use_silence
from app.llm import local_gguf_client
from app.llm.prompt_builder import build_prompt
from app.llm.structured_output import ModelReply, parse_model_reply
from app.memory.long_term_memory_store import get_important_memories
from app.memory.memory_extractor import extract_memory_updates
from app.memory.memory_selector import select_memories_for_reply
from app.memory.profile_store import apply_memory_updates, get_profile
from app.memory.short_term_dialogue_store import (
    add_dialogue_turn,
    get_recent_bot_messages,
)
from app.output.hardware_action_mapper import map_to_hardware_actions
from app.persona.persona_store import apply_persona_updates, get_current_persona
from app.persona.persona_update_extractor import extract_persona_updates
from app.proactive.proactive_dialogue_planner import choose_proactive_type
from app.proactive.proactive_store import log_proactive_decision
from app.proactive.question_planner import choose_question_type
from app.proactive.should_speak import should_speak
from app.relationship.relationship_store import (
    get_relationship_state,
    save_relationship_state,
)
from app.relationship.relationship_updater import update_relationship_after_interaction
from app.schemas.engine import EngineInput, EngineOutput
from app.strategy.choose_strategy import choose_strategy
from app.understanding.detect_emotion import detect_emotion
from app.understanding.detect_intent import detect_intent
from app.understanding.detect_risk import detect_risk
from app.understanding.emotion_trace_store import (
    add_emotion_trace,
    get_recent_emotion_traces,
)
from app.understanding.emotion_trend import detect_emotion_trend


def _now_iso() -> str:
    """生成当前 UTC 时间字符串，用于写入聊天日志。"""
    return datetime.now(UTC).isoformat()


def _write_conversation_log(
    user_id: str,
    role: str,
    content: str,
    intent: str | None,
    emotion: str | None,
    risk_level: str | None,
    strategy: str | None,
    db_path: str,
) -> None:
    """写入一条聊天日志，记录用户消息或机器人回复。"""
    conn = get_connection(db_path)

    try:
        conn.execute(
            """
            INSERT INTO conversation_logs (
                user_id,
                role,
                content,
                intent,
                emotion,
                risk_level,
                strategy,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                role,
                content,
                intent,
                emotion,
                risk_level,
                strategy,
                _now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _as_value(value: object) -> str | None:
    """兼容 Enum 和字符串，统一取出文本值。"""
    return getattr(value, "value", value)


def _inner_emotion_for(emotion: object, risk_level: object) -> str:
    """Use backend understanding to fill structured reply metadata."""
    risk_value = _as_value(risk_level)
    emotion_value = _as_value(emotion)
    if risk_value in ["high", "medium"] or emotion_value in ["sad", "anxious", "angry"]:
        return "worried"
    if emotion_value == "happy":
        return "playful"
    return "warm"


def _suggested_expression_for(emotion: object, risk_level: object) -> str:
    """Map backend understanding to a hardware-friendly expression hint."""
    risk_value = _as_value(risk_level)
    emotion_value = _as_value(emotion)
    if risk_value in ["high", "medium"] or emotion_value in ["sad", "anxious", "angry"]:
        return "worried"
    if emotion_value == "happy":
        return "playful"
    return "warm"


def handle_event(
    input_data: EngineInput,
    db_path: str,
    use_local_model: bool = True,
) -> EngineOutput:
    """处理一次事件输入，返回完整引擎输出。"""
    init_db(db_path)

    user_profile = get_profile(input_data.user_id, db_path)
    persona = get_current_persona(input_data.user_id, db_path)
    relationship_state = get_relationship_state(input_data.user_id, db_path)
    important_memories = get_important_memories(input_data.user_id, limit=5, db_path=db_path)
    context = build_context(
        input_data=input_data,
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
        memories=important_memories,
    )

    intent = detect_intent(input_data.user_text)
    emotion = detect_emotion(input_data.user_text)
    risk_level = detect_risk(input_data.user_text)
    add_emotion_trace(input_data.user_id, emotion, risk_level, db_path)
    emotion_traces = get_recent_emotion_traces(input_data.user_id, limit=5, db_path=db_path)
    emotion_trend = detect_emotion_trend(emotion_traces)
    feedback_type, quality_score = evaluate_user_reaction(input_data.user_text)

    # 高/中风险场景不让关系评估影响安全流程，只记录中性反馈调试值。
    if _as_value(risk_level) not in ["high", "medium"]:
        relationship_state = update_relationship_after_interaction(
            state=relationship_state,
            feedback_type=feedback_type,
        )
        save_relationship_state(relationship_state, db_path)
        save_interaction_feedback(
            user_id=input_data.user_id,
            robot_response="",
            user_reaction=input_data.user_text,
            quality_score=quality_score,
            feedback_type=feedback_type,
            db_path=db_path,
        )
    selected_memories = select_memories_for_reply(
        memories=important_memories,
        emotion=emotion,
        intent=intent,
        relationship_state=relationship_state,
        limit=3,
    )
    can_speak, speak_reason = should_speak(
        context=context,
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
        db_path=db_path,
    )

    if not can_speak:
        log_proactive_decision(
            user_id=input_data.user_id,
            event_type=input_data.event_type,
            should_speak=False,
            proactive_type=None,
            question_type=None,
            reason=speak_reason,
            db_path=db_path,
        )
        return EngineOutput(
            should_speak=False,
            response_text=None,
            detected_intent=_as_value(intent),
            detected_emotion=_as_value(emotion),
            risk_level=_as_value(risk_level) or "none",
            debug={
                "speak_reason": speak_reason,
                "feedback_type": feedback_type,
                "quality_score": quality_score,
                "emotion_trend": emotion_trend,
                "important_memory_count": len(important_memories),
            },
        )

    question_type = choose_question_type(
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
        intent=intent,
        emotion=emotion,
    )
    proactive_type = choose_proactive_type(
        context=context,
        user_profile=user_profile,
        relationship_state=relationship_state,
        question_type=question_type,
    )
    strategy = choose_strategy(
        intent=intent,
        emotion=emotion,
        risk_level=risk_level,
        proactive_type=proactive_type,
        question_type=question_type,
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
    )
    prompt = build_prompt(
        user_text=input_data.user_text,
        context=context,
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
        memories=selected_memories,
        intent=intent,
        emotion=emotion,
        risk_level=risk_level,
        strategy=strategy,
        emotion_trend=emotion_trend,
    )
    _ = use_local_model
    local_model_reply_usable: bool | None = None
    used_model_fallback = False

    raw_model_text = local_gguf_client.generate_response(prompt)
    parsed_reply = parse_model_reply(raw_model_text)
    raw_reply = parsed_reply.reply_text
    local_model_reply_usable = local_gguf_client.is_response_usable(raw_reply)
    if not local_model_reply_usable:
        raise local_gguf_client.LocalModelError("本地模型输出不可用，已拒绝返回 mock 或内部分析文本")
    user_visible_raw_reply = raw_reply
    recent_bot_messages = get_recent_bot_messages(input_data.user_id, limit=3, db_path=db_path)
    used_silence = should_use_silence(
        intent=intent,
        emotion=emotion,
        risk_level=risk_level,
        relationship_state=relationship_state,
        user_profile=user_profile,
    )
    asked_question = should_ask_question(
        recent_bot_messages=recent_bot_messages,
        intent=intent,
        emotion=emotion,
        relationship_state=relationship_state,
        strategy=strategy,
    )
    recalled_memory = should_recall_memory(
        memories=selected_memories,
        intent=intent,
        emotion=emotion,
        relationship_state=relationship_state,
        strategy=strategy,
    )
    model_reply = ModelReply(
        reply_text=raw_reply,
        inner_emotion=_inner_emotion_for(emotion, risk_level),
        suggested_expression=_suggested_expression_for(emotion, risk_level),
        should_ask_followup=asked_question,
        memory_reference_used=recalled_memory,
        confidence=parsed_reply.confidence,
    )
    response_text = make_reply_humanlike(
        raw_reply=user_visible_raw_reply,
        intent=intent,
        emotion=emotion,
        risk_level=risk_level,
        strategy=strategy,
        user_profile=user_profile,
        persona=persona,
        relationship_state=relationship_state,
        memories=selected_memories,
        recent_bot_messages=recent_bot_messages,
        emotion_trend=emotion_trend,
    )

    memory_updates = extract_memory_updates(input_data.user_text)
    updated_profile = apply_memory_updates(input_data.user_id, memory_updates, db_path)
    persona_updates = extract_persona_updates(input_data.user_text)
    updated_persona = apply_persona_updates(input_data.user_id, persona_updates, db_path)

    if input_data.user_text:
        add_dialogue_turn(
            user_id=input_data.user_id,
            role="user",
            content=input_data.user_text,
            strategy=None,
            db_path=db_path,
        )
        _write_conversation_log(
            user_id=input_data.user_id,
            role="user",
            content=input_data.user_text,
            intent=_as_value(intent),
            emotion=_as_value(emotion),
            risk_level=_as_value(risk_level),
            strategy=None,
            db_path=db_path,
        )

    add_dialogue_turn(
        user_id=input_data.user_id,
        role="assistant",
        content=response_text,
        strategy=_as_value(strategy),
        db_path=db_path,
    )
    _write_conversation_log(
        user_id=input_data.user_id,
        role="assistant",
        content=response_text,
        intent=_as_value(intent),
        emotion=_as_value(emotion),
        risk_level=_as_value(risk_level),
        strategy=_as_value(strategy),
        db_path=db_path,
    )

    log_proactive_decision(
        user_id=input_data.user_id,
        event_type=input_data.event_type,
        should_speak=True,
        proactive_type=proactive_type,
        question_type=question_type,
        reason="allowed",
        db_path=db_path,
    )

    hardware_actions = map_to_hardware_actions(
        response_text=response_text,
        strategy=strategy,
        risk_level=risk_level,
    )

    return EngineOutput(
        should_speak=True,
        response_text=response_text,
        detected_intent=_as_value(intent),
        detected_emotion=_as_value(emotion),
        risk_level=_as_value(risk_level) or "none",
        strategy=_as_value(strategy),
        proactive_type=proactive_type,
        question_type=question_type,
        memory_updates=[update.model_dump() for update in memory_updates],
        persona_updates=[update.model_dump() for update in persona_updates],
        hardware_actions=hardware_actions,
        debug={
            "speak_reason": speak_reason,
            "feedback_type": feedback_type,
            "quality_score": quality_score,
            "emotion_trend": emotion_trend,
            "raw_reply": raw_reply,
            "final_reply": response_text,
            "model_reply": model_reply.model_dump(),
            "local_model_reply_usable": local_model_reply_usable,
            "used_model_fallback": used_model_fallback,
            "humanlike_applied": True,
            "used_silence": used_silence,
            "asked_question": asked_question,
            "recalled_memory": recalled_memory,
            "prompt": prompt,
            "use_local_model": True,
            "mock_disabled": True,
            "local_model_error": local_gguf_client.get_last_error(),
            "important_memory_count": len(important_memories),
            "selected_memory_count": len(selected_memories),
            "updated_profile": updated_profile.model_dump(),
            "updated_persona": updated_persona.model_dump(),
        },
    )
