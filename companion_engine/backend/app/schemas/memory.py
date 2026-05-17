"""记忆 Schema 文件，定义用户画像和记忆更新数据结构。"""

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户画像，记录长期陪伴中逐步形成的用户偏好。"""

    user_id: str = Field(description="用户唯一标识。")
    preferred_address: str | None = Field(default=None, description="用户偏好的称呼方式。")
    preferred_support_style: str = Field(default="unknown", description="用户偏好的支持方式。")
    initiative_tolerance: str = Field(default="medium", description="用户对机器人主动互动的接受程度。")
    disliked_responses: list[str] = Field(default_factory=list, description="用户不喜欢的回复方式。")
    liked_topics: list[str] = Field(default_factory=list, description="用户喜欢聊的话题。")
    avoided_topics: list[str] = Field(default_factory=list, description="用户希望避开的主题。")
    last_known_mood: str | None = Field(default=None, description="最近一次识别到的用户情绪。")


class MemoryUpdate(BaseModel):
    """记忆更新，表示从一次对话中抽取出的可保存信息。"""

    key: str = Field(description="记忆字段或主题名称。")
    value: str | list[str] = Field(description="记忆内容，可以是单个文本或文本列表。")
    confidence: float = Field(ge=0, le=1, description="记忆可信度，范围为 0 到 1。")
    source_text: str = Field(description="产生这条记忆的原始用户文本或上下文。")
