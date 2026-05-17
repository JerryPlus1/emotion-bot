"""关系 Schema 文件，定义用户与机器人的陪伴关系状态。"""

from pydantic import BaseModel, Field


class RelationshipState(BaseModel):
    """关系状态，描述当前陪伴关系的发展阶段和互动质量。"""

    user_id: str = Field(description="用户唯一标识。")
    relationship_stage: str = Field(default="stranger", description="当前关系阶段。")
    trust_level: float = Field(default=0.2, ge=0, le=1, description="信任程度，范围为 0 到 1。")
    intimacy_level: float = Field(default=0.1, ge=0, le=1, description="亲密程度，范围为 0 到 1。")
    user_openness: float = Field(default=0.2, ge=0, le=1, description="用户开放程度，范围为 0 到 1。")
    recent_interaction_quality: str = Field(default="neutral", description="最近互动质量。")
    last_meaningful_topic: str | None = Field(default=None, description="最近一次有意义的对话主题。")
