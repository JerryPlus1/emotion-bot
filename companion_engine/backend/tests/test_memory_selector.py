"""记忆选择测试，验证真人感优化中的记忆引用克制规则。"""

from app.memory.memory_selector import select_memories_for_reply
from app.schemas.emotion import ConversationIntent, EmotionType
from app.schemas.long_term_memory import LongTermMemory
from app.schemas.relationship import RelationshipState


def _memory(content: str, valence: str, importance: float) -> LongTermMemory:
    """创建测试用长期记忆。"""
    return LongTermMemory(
        memory_type="preference",
        content=content,
        importance=importance,
        emotional_valence=valence,
        source_text=content,
    )


def test_wants_space_returns_no_memories() -> None:
    """测试用户想安静时不引用记忆。"""
    memories = [_memory("用户喜欢散步", "warm", 0.9)]

    selected = select_memories_for_reply(
        memories=memories,
        emotion=EmotionType.neutral,
        intent=ConversationIntent.wants_space,
        relationship_state=RelationshipState(user_id="user_a"),
    )

    assert selected == []


def test_low_emotion_prioritizes_supportive_memories() -> None:
    """测试情绪低落时优先选择支持型记忆。"""
    cold_memory = _memory("用户提过一次压力", "negative", 0.95)
    warm_memory = _memory("用户喜欢安静陪伴", "supportive", 0.5)

    selected = select_memories_for_reply(
        memories=[cold_memory, warm_memory],
        emotion=EmotionType.sad,
        intent=ConversationIntent.casual_chat,
        relationship_state=RelationshipState(user_id="user_a", relationship_stage="trusted"),
        limit=2,
    )

    assert selected[0] == warm_memory


def test_stranger_uses_at_most_one_memory() -> None:
    """测试陌生关系最多选择一条记忆。"""
    memories = [
        _memory("记忆一", "neutral", 0.8),
        _memory("记忆二", "neutral", 0.7),
    ]

    selected = select_memories_for_reply(
        memories=memories,
        emotion="neutral",
        intent="casual_chat",
        relationship_state=RelationshipState(user_id="user_a", relationship_stage="stranger"),
        limit=3,
    )

    assert len(selected) == 1
