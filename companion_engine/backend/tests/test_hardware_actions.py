"""硬件动作测试，验证策略映射和占位适配器稳定可用。"""

from app.output.hardware_action_mapper import map_to_hardware_actions
from app.output.mqtt_adapter import send_hardware_actions_mqtt
from app.output.serial_adapter import send_hardware_actions_serial
from app.schemas.hardware import HardwareActions
from app.schemas.strategy import EmpathyStrategy


def test_high_risk_maps_to_worried_actions() -> None:
    """测试高风险映射为担心表情和红灯前倾。"""
    actions = map_to_hardware_actions("注意安全", "quiet_company", "high")

    assert actions.expression == "worried"
    assert actions.light_color == "red"
    assert actions.motion == "lean_forward"
    assert actions.speech_text == "注意安全"


def test_emotional_validation_maps_to_warm_actions() -> None:
    """测试安慰策略映射为温暖点头。"""
    actions = map_to_hardware_actions(
        "听起来很不好受。",
        EmpathyStrategy.emotional_validation,
        "none",
    )

    assert actions.expression == "warm"
    assert actions.light_color == "soft_white"
    assert actions.motion == "nod"


def test_playful_maps_to_playful_actions() -> None:
    """测试 playful 策略映射为黄色灯和 playful 表情。"""
    actions = map_to_hardware_actions("小玩伴模式启动。", "playful_response", "none")

    assert actions.expression == "playful"
    assert actions.light_color == "yellow"
    assert actions.motion == "nod"


def test_quiet_company_maps_to_quiet_actions() -> None:
    """测试 quiet_company 策略映射为蓝灯安静待机。"""
    actions = map_to_hardware_actions("我在这儿。", "quiet_company", "none")

    assert actions.expression == "neutral"
    assert actions.light_color == "blue"
    assert actions.motion == "idle"


def test_serial_and_mqtt_placeholders_do_not_crash() -> None:
    """测试串口和 MQTT 占位函数不会报错。"""
    actions = HardwareActions(speech_text="测试")

    assert send_hardware_actions_serial(actions, "COM3") is False
    assert send_hardware_actions_mqtt(actions, "robot/actions") is False
