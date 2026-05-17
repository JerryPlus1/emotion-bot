"""健康检查测试，确保 FastAPI 服务基础接口可用。"""

from fastapi.testclient import TestClient

from main import app


def test_health_check() -> None:
    """测试 /health 返回 ok 状态。"""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
