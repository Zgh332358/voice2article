"""Generation 端点端到端测试 —— mock LLM client，不打 Step API。"""

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm import LLMError, StepLLMClient, get_llm_client


def _register(client: TestClient, email: str = "gen@aiken.dev") -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "passw0rd1", "nickname": "Gen Tester"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_conv(client: TestClient, token: str, contents: list[str]) -> str:
    """创建一个会话，往里塞 user 消息，返回 conv id。"""
    cv = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"title": "test", "mode": "dialogue"},
    )
    assert cv.status_code == 201
    conv_id = cv.json()["id"]
    for c in contents:
        m = client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=_auth(token),
            json={"role": "user", "content": c},
        )
        assert m.status_code == 201
    return conv_id


@pytest.fixture
def fake_llm() -> AsyncMock:
    fake = AsyncMock(spec=StepLLMClient)
    fake.model = "step-test"
    fake.complete.return_value = (
        "如何让 Step-2 写出爆款公众号\n\n"
        "## 引言\n这是一篇示例文章。\n\n## 结论\n搞定。"
    )

    async def _stream(_messages: Any, **_kw: Any) -> AsyncIterator[str]:
        for piece in ["如何让", " Step-2", " 写出爆款", "\n\n## 引言", "\n搞定。"]:
            yield piece

    fake.stream.side_effect = _stream
    app.dependency_overrides[get_llm_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_llm_client, None)


def test_create_generation_happy(client: TestClient, fake_llm: AsyncMock) -> None:
    token = _register(client)
    conv_id = _seed_conv(client, token, ["今天讲讲 Step-2", "重点是长文本能力"])

    resp = client.post(
        "/api/v1/generations",
        headers=_auth(token),
        json={"conversation_id": conv_id, "mode": "dialogue", "tone": "亲切"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "如何让 Step-2 写出爆款公众号"
    assert "示例文章" in body["generated_content"]
    assert body["status"] == "draft"
    assert body["word_count"] > 0
    fake_llm.complete.assert_awaited_once()


def test_create_generation_persists_in_history(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    token = _register(client)
    conv_id = _seed_conv(client, token, ["内容 A"])

    client.post(
        "/api/v1/generations",
        headers=_auth(token),
        json={"conversation_id": conv_id},
    )
    history = client.get("/api/v1/generations", headers=_auth(token))
    assert history.status_code == 200
    h = history.json()
    assert h["total"] == 1
    assert h["items"][0]["conversation_id"] == conv_id


def test_generation_filters_by_conversation(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    token = _register(client)
    a = _seed_conv(client, token, ["x"])
    b = _seed_conv(client, token, ["y"])

    for cid in (a, b, b):
        client.post(
            "/api/v1/generations",
            headers=_auth(token),
            json={"conversation_id": cid},
        )

    only_b = client.get(
        f"/api/v1/generations?conversation_id={b}", headers=_auth(token)
    ).json()
    assert only_b["total"] == 2
    assert all(item["conversation_id"] == b for item in only_b["items"])


def test_create_generation_empty_conversation_returns_422(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    token = _register(client)
    cv = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"title": "empty", "mode": "dialogue"},
    )
    conv_id = cv.json()["id"]

    resp = client.post(
        "/api/v1/generations",
        headers=_auth(token),
        json={"conversation_id": conv_id},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "empty_conversation"
    fake_llm.complete.assert_not_called()


def test_create_generation_cross_user_404(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    alice = _register(client, "alice-gen@aiken.dev")
    eve = _register(client, "eve-gen@aiken.dev")
    conv_id = _seed_conv(client, alice, ["alice 的内容"])

    resp = client.post(
        "/api/v1/generations",
        headers=_auth(eve),
        json={"conversation_id": conv_id},
    )
    assert resp.status_code == 404
    fake_llm.complete.assert_not_called()


def test_create_generation_propagates_upstream_error(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    fake_llm.complete.side_effect = LLMError("LLM 上游错误（500）", code="llm_upstream")
    token = _register(client)
    conv_id = _seed_conv(client, token, ["内容"])

    resp = client.post(
        "/api/v1/generations",
        headers=_auth(token),
        json={"conversation_id": conv_id},
    )
    assert resp.status_code == 502
    assert resp.json()["code"] == "llm_upstream"


def test_stream_generation_emits_deltas_and_done(
    client: TestClient, fake_llm: AsyncMock
) -> None:
    token = _register(client)
    conv_id = _seed_conv(client, token, ["流式生成测试"])

    with client.stream(
        "POST",
        "/api/v1/generations/stream",
        headers=_auth(token),
        json={"conversation_id": conv_id},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        events: list[dict[str, Any]] = []
        for raw in resp.iter_lines():
            line = raw.strip() if isinstance(raw, str) else raw.decode().strip()
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))

    types = [e["type"] for e in events]
    assert types[:5] == ["delta"] * 5  # 5 个 chunk
    assert types[-1] == "done"
    done = events[-1]
    assert done["generation_id"]
    assert done["word_count"] > 0
