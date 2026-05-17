"""硬件 Schema 文件，定义机器人表情、灯光、动作和语音输出。"""

from pydantic import BaseModel, Field


class HardwareActions(BaseModel):
    """硬件动作，表示对机器人外设层的最小输出指令。"""

    expression: str = Field(default="neutral", description="机器人表情状态。")
    light_color: str = Field(default="soft_white", description="灯光颜色。")
    motion: str = Field(default="idle", description="身体或底盘动作。")
    speech_text: str | None = Field(default=None, description="需要通过语音播放的文本。")
