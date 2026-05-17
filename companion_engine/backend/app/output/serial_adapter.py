"""串口适配文件，预留通过串口发送硬件动作的接口。"""

from app.schemas.hardware import HardwareActions


def send_hardware_actions_serial(actions: HardwareActions, port: str) -> bool:
    """串口输出占位函数，当前阶段不依赖 pyserial，也不真实发送。"""
    # 保留参数是为了固定未来硬件层接口形状。
    _ = actions
    _ = port

    # 串口适配尚未启用，返回 False 表示没有实际发送。
    return False
