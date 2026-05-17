"""MQTT 适配文件，预留通过 MQTT 发送硬件动作的接口。"""

from app.schemas.hardware import HardwareActions


def send_hardware_actions_mqtt(actions: HardwareActions, topic: str) -> bool:
    """MQTT 输出占位函数，当前阶段不依赖 MQTT 库，也不真实发送。"""
    # 保留参数是为了固定未来硬件层接口形状。
    _ = actions
    _ = topic

    # MQTT 适配尚未启用，返回 False 表示没有实际发送。
    return False
