"""FastAPI 接口测试，验证前端和硬件层可通过 HTTP 调用引擎。"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from main import app


def _client_with_temp_db(tmp_path: Path, monkeypatch) -> TestClient:
    """创建使用临时数据库路径的测试客户端。"""
    monkeypatch.setattr(routes, "DEFAULT_DB_PATH", str(tmp_path / "api.db"))
    return TestClient(app)


def test_health_returns_ok() -> None:
    """测试健康检查接口返回 ok。"""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_chat_user_direct_chat_returns_should_speak_true(tmp_path: Path, monkeypatch) -> None:
    """测试 /api/chat 用户主动聊天会返回 should_speak=True。"""
    client = _client_with_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/chat",
        json={
            "user_id": "default_user",
            "event_type": "user_direct_chat",
            "user_text": "你好",
            "scene": {
                "time": "10:00",
                "location": "书桌旁",
                "activity": "聊天",
                "is_user_nearby": True,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["should_speak"] is True


def test_api_state_returns_state_structure(tmp_path: Path, monkeypatch) -> None:
    """测试 /api/state/{user_id} 返回用户状态结构。"""
    client = _client_with_temp_db(tmp_path, monkeypatch)

    response = client.get("/api/state/default_user")

    assert response.status_code == 200
    data = response.json()
    assert "user_profile" in data
    assert "persona" in data
    assert "relationship_state" in data
    assert "recent_memories" in data
    assert "important_memories" in data


def test_api_persona_can_save_persona(tmp_path: Path, monkeypatch) -> None:
    """测试 /api/persona/{user_id} 可以保存 Persona。"""
    client = _client_with_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/persona/default_user",
        json={
            "role_style": "soft_companion",
            "warmth_level": "high",
            "initiative_level": "medium",
            "analysis_level": "medium",
            "playfulness_level": "medium",
            "speech_length": "medium",
            "companionship_style": "listen_first",
        },
    )
    state_response = client.get("/api/state/default_user")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert state_response.json()["persona"]["warmth_level"] == "high"


def test_api_reset_returns_ok(tmp_path: Path, monkeypatch) -> None:
    """测试 /api/reset/{user_id} 可以删除用户测试数据并返回 ok。"""
    client = _client_with_temp_db(tmp_path, monkeypatch)
    client.post(
        "/api/chat",
        json={
            "user_id": "default_user",
            "event_type": "user_direct_chat",
            "user_text": "你能不能温柔一点",
            "scene": {"time": "10:00", "is_user_nearby": True},
        },
    )

    response = client.post("/api/reset/default_user")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
