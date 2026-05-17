"""长期记忆 Schema 文件，定义可持久化的重要记忆结构。"""

from pydantic import BaseModel, Field


class LongTermMemory(BaseModel):
    """长期记忆，表示值得跨会话保存的重要信息。"""

    memory_type: str = Field(description="记忆类型，例如偏好、经历或重要事实。")
    content: str = Field(description="记忆的具体内容。")
    importance: float = Field(ge=0, le=1, description="记忆重要程度，范围为 0 到 1。")
    emotional_valence: str = Field(default="neutral", description="记忆的情绪倾向。")
    source_text: str = Field(description="产生这条长期记忆的原始文本。")
