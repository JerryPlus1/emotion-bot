"""对话引擎 Schema 文件，定义引擎输入、上下文和输出数据结构。"""

from typing import Any

from pydantic import BaseModel, Field


class SceneContext(BaseModel):
    """场景上下文，描述机器人当前能感知到的外部环境。"""

    time: str | None = Field(default=None, description="当前时间描述，例如早晨、晚上或具体时间。")
    location: str | None = Field(default=None, description="当前地点描述，例如客厅、卧室或书桌旁。")
    activity: str | None = Field(default=None, description="用户或场景中的当前活动。")
    is_user_nearby: bool = Field(default=False, description="用户是否在机器人附近。")


class EngineInput(BaseModel):
    """引擎输入，表示一次外部事件进入对话引擎时携带的数据。"""

    user_id: str = Field(default="default_user", description="用户唯一标识，默认使用单用户模式。")
    event_type: str = Field(description="事件类型，例如用户输入、定时触发或传感器事件。")
    user_text: str | None = Field(default=None, description="用户输入文本，没有文本事件时为空。")
    scene: SceneContext = Field(description="当前场景上下文。")


class DialogueContext(BaseModel):
    """对话上下文，表示引擎内部生成回复前使用的综合上下文。"""

    user_id: str = Field(description="用户唯一标识。")
    event_type: str = Field(description="触发当前对话流程的事件类型。")
    user_text: str | None = Field(description="用户输入文本，没有文本事件时为空。")
    scene: SceneContext = Field(description="当前场景上下文。")
    recent_memories: list[Any] = Field(default_factory=list, description="近期对话或互动记忆列表。")
    important_memories: list[Any] = Field(default_factory=list, description="与当前对话相关的重要记忆列表。")


class EngineOutput(BaseModel):
    """引擎输出，表示一次对话决策后的文本、策略、记忆更新和硬件动作。"""

    should_speak: bool = Field(description="机器人是否应该对外说话。")
    response_text: str | None = Field(default=None, description="准备输出给用户的回复文本。")
    detected_intent: str | None = Field(default=None, description="识别到的用户意图。")
    detected_emotion: str | None = Field(default=None, description="识别到的用户情绪。")
    risk_level: str = Field(default="none", description="风险等级，默认无风险。")
    strategy: str | None = Field(default=None, description="本轮回复采用的策略。")
    proactive_type: str | None = Field(default=None, description="主动互动类型，没有主动互动时为空。")
    question_type: str | None = Field(default=None, description="提问类型，没有提问时为空。")
    memory_updates: list[Any] = Field(default_factory=list, description="本轮需要写入的记忆更新。")
    persona_updates: list[Any] = Field(default_factory=list, description="本轮需要写入的人格偏好更新。")
    hardware_actions: object | None = Field(default=None, description="需要输出给硬件层的动作指令。")
    debug: dict[str, Any] = Field(default_factory=dict, description="调试信息，供开发阶段观察内部决策。")
