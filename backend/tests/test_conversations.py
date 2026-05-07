"""会话 CRUD + 消息追加 + 跨用户越权拦截测试。"""

from collections.abc import Callable

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "passw0rd1", "nickname": email.split("@")[0]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_create(client: TestClient, token: str) -> Callable[[str | None], dict]:
    def _create(title: str | None) -> dict:
        resp = client.post(
            "/api/v1/conversations",
            headers=_auth(token),
            json={"title": title, "mode": "dialogue"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _create


def test_create_list_get_and_append_message(client: TestClient) -> None:
    token = _register(client, "alice-conv@aiken.dev")
    create = _make_create(client, token)

    a = create("草稿 A")
    create("草稿 B")
    assert a["title"] == "草稿 A"
    assert a["mode"] == "dialogue"

    list_resp = client.get("/api/v1/conversations", headers=_auth(token))
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"草稿 A", "草稿 B"}

    append_resp = client.post(
        f"/api/v1/conversations/{a['id']}/messages",
        headers=_auth(token),
        json={"role": "user", "content": "今天我们要写一篇关于 Step-2 的评测"},
    )
    assert append_resp.status_code == 201
    msg = append_resp.json()
    assert msg["role"] == "user"
    assert msg["conversation_id"] == a["id"]

    detail_resp = client.get(f"/api/v1/conversations/{a['id']}", headers=_auth(token))
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["content"].startswith("今天")


def test_update_and_delete_conversation(client: TestClient) -> None:
    token = _register(client, "bob-conv@aiken.dev")
    conv = _make_create(client, token)("旧标题")

    upd = client.patch(
        f"/api/v1/conversations/{conv['id']}",
        headers=_auth(token),
        json={"title": "新标题"},
    )
    assert upd.status_code == 200
    assert upd.json()["title"] == "新标题"

    delete_resp = client.delete(f"/api/v1/conversations/{conv['id']}", headers=_auth(token))
    assert delete_resp.status_code == 204

    miss = client.get(f"/api/v1/conversations/{conv['id']}", headers=_auth(token))
    assert miss.status_code == 404
    assert miss.json()["code"] == "conversation_not_found"


def test_cross_user_access_returns_404(client: TestClient) -> None:
    alice_token = _register(client, "alice2-conv@aiken.dev")
    eve_token = _register(client, "eve-conv@aiken.dev")
    conv = _make_create(client, alice_token)("Alice 私密")

    # Eve 试图读 / 改 / 删 / 追加，全部应该看到 404，不暴露存在性
    for method, url, payload in [
        ("get", f"/api/v1/conversations/{conv['id']}", None),
        ("patch", f"/api/v1/conversations/{conv['id']}", {"title": "hijacked"}),
        ("delete", f"/api/v1/conversations/{conv['id']}", None),
        (
            "post",
            f"/api/v1/conversations/{conv['id']}/messages",
            {"role": "user", "content": "leak"},
        ),
    ]:
        request_kwargs: dict = {"headers": _auth(eve_token)}
        if payload is not None:
            request_kwargs["json"] = payload
        resp = client.request(method, url, **request_kwargs)
        assert resp.status_code == 404, f"{method} {url} 应该 404，实际 {resp.status_code}"

    # Alice 自己列表里仍然看得到
    own = client.get("/api/v1/conversations", headers=_auth(alice_token)).json()
    assert own["total"] == 1


def test_endpoints_require_auth(client: TestClient) -> None:
    for method, url in [
        ("get", "/api/v1/conversations"),
        ("post", "/api/v1/conversations"),
    ]:
        resp = client.request(method, url, json={} if method == "post" else None)
        assert resp.status_code == 401
