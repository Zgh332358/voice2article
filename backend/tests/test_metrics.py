"""metrics 端点烟雾测试。"""

from fastapi.testclient import TestClient


def test_metrics_endpoint_returns_basic_fields(client: TestClient) -> None:
    # 先打几次别的接口让计数动起来
    client.get("/api/v1/health")
    client.get("/api/v1/health")

    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    body = resp.json()

    assert body["name"] == "voice-backend"
    assert "version" in body
    assert body["env"] in {"development", "test", "production"}
    assert body["uptime_seconds"] >= 0
    assert body["request_count"] >= 3  # 2 health + 1 metrics
    assert body["python_version"].count(".") == 2
