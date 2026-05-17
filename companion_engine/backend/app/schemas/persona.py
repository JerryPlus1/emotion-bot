"""人格 Schema 文件，定义机器人角色快照和偏好更新数据结构。"""

from pydantic import BaseModel, Field


class PersonaSnapshot(BaseModel):
    """机器人当前人格快照，描述陪伴风格和表达方式。"""

    role_style: str = Field(default="soft_companion", description="机器人角色风格。")
    warmth_level: str = Field(default="medium", description="表达温暖程度。")
    initiative_level: str = Field(default="medium", description="主动发起互动的程度。")
    analysis_level: str = Field(default="medium", description="分析和解释的详细程度。")
    playfulness_level: str = Field(default="medium", description="轻松玩笑和活泼表达的程度。")
    speech_length: str = Field(default="medium", description="回复长度偏好。")
    companionship_style: str = Field(default="listen_first", description="陪伴方式偏好。")


class PersonaUpdate(BaseModel):
    """人格更新，表示一次互动中抽取出的角色偏好调整。"""

    dimension: str = Field(description="需要更新的人格维度。")
    value: str = Field(description="该人格维度的新取值。")
    confidence: float = Field(ge=0, le=1, description="更新可信度，范围为 0 到 1。")
    evidence: str = Field(description="支持该更新的证据文本。")
    source_type: str = Field(description="更新来源类型，例如用户反馈或系统观察。")


class PersonaPreference(BaseModel):
    """人格偏好，表示已确认或待确认的角色表达偏好。"""

    dimension: str = Field(description="人格偏好维度。")
    value: str = Field(description="偏好取值。")
    confidence: float = Field(ge=0, le=1, description="偏好可信度，范围为 0 到 1。")
    evidence: str = Field(description="支持该偏好的证据文本。")
    source_type: str = Field(description="偏好来源类型，例如用户反馈或长期观察。")
