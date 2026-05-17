"""本地 GGUF 客户端测试，确保模型不可用时服务不会崩溃。"""

from pathlib import Path

import pytest

from app.core import engine
from app.llm import local_gguf_client
from app.schemas.engine import EngineInput, SceneContext


def _db_path(tmp_path: Path) -> str:
    """返回测试用临时数据库路径，避免污染真实 data 目录。"""
    return str(tmp_path / "companion.db")


def test_generate_response_raises_when_model_path_missing(monkeypatch, tmp_path: Path) -> None:
    """测试模型路径不存在时抛错，不返回假数据。"""
    missing_path = tmp_path / "missing.gguf"
    monkeypatch.setenv("LOCAL_GGUF_MODEL_PATH", str(missing_path))

    with pytest.raises(local_gguf_client.LocalModelError):
        local_gguf_client.generate_response("你好")


def test_is_local_model_available_returns_false_when_path_missing(monkeypatch, tmp_path: Path) -> None:
    """测试模型路径不存在时可用性返回 False。"""
    missing_path = tmp_path / "missing.gguf"
    monkeypatch.setenv("LOCAL_GGUF_MODEL_PATH", str(missing_path))

    assert local_gguf_client.is_local_model_available() is False


def test_engine_use_local_model_false_still_uses_local_model(monkeypatch, tmp_path: Path) -> None:
    """测试 use_local_model=False 也会被强制改为本地模型路径。"""
    called = False

    def fake_generate_response(prompt: str) -> str:
        nonlocal called
        called = True
        assert "用户刚刚说：" in prompt
        return "这是强制本地模型回复。"

    monkeypatch.setattr(
        engine.local_gguf_client,
        "generate_response",
        fake_generate_response,
    )

    output = engine.handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="你好",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
        use_local_model=False,
    )

    assert called is True
    assert output.should_speak is True
    assert output.response_text == "这是强制本地模型回复。"
    assert output.debug["use_local_model"] is True
    assert output.debug["mock_disabled"] is True
    assert output.debug["used_model_fallback"] is False


def test_engine_can_return_monkeypatched_local_model_response(monkeypatch, tmp_path: Path) -> None:
    """测试 monkeypatch 本地模型生成函数后，引擎可以返回模拟本地模型回复。"""

    def fake_generate_response(prompt: str) -> str:
        """模拟本地模型回复，避免测试加载真实大模型。"""
        assert "用户刚刚说：" in prompt
        return "这是本地模型模拟回复。"

    monkeypatch.setattr(
        engine.local_gguf_client,
        "generate_response",
        fake_generate_response,
    )

    output = engine.handle_event(
        EngineInput(
            event_type="user_direct_chat",
            user_text="你好",
            scene=SceneContext(time="10:00", is_user_nearby=True),
        ),
        _db_path(tmp_path),
        use_local_model=True,
    )

    assert output.response_text == "这是本地模型模拟回复。"
