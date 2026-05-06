"""健康检查端点的烟雾测试。"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["name"] == "voice-backend"
    assert "version" in body
    assert "env" in body
