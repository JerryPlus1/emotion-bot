"""HTTP 适配文件，负责预留通过 HTTP 发送硬件动作的接口。"""

import httpx

from app.schemas.hardware import HardwareActions


def send_hardware_actions_http(actions: HardwareActions, endpoint: str) -> bool:
    """通过 HTTP POST 发送硬件动作，失败时返回 False。"""
    try:
        response = httpx.post(
            endpoint,
            json=actions.model_dump(),
            timeout=3.0,
        )
        response.raise_for_status()
    except Exception:
        # 硬件层不可用时不能影响对话主流程。
        return False

    return True
