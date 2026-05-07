"""排版端点测试：列模板 / 应用 / 未知模板 / 鉴权 / HTML 关键片段。"""

from fastapi.testclient import TestClient


def _register(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "fmt@aiken.dev", "password": "passw0rd1"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_templates_returns_three(client: TestClient) -> None:
    token = _register(client)
    resp = client.get("/api/v1/formatting/templates", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    ids = {it["id"] for it in items}
    assert ids == {"minimal", "business", "tech"}


def test_list_templates_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/formatting/templates")
    assert resp.status_code == 401


def test_apply_template_renders_inline_styles(client: TestClient) -> None:
    token = _register(client)
    payload = {
        "template_id": "minimal",
        "title": "Step-2 评测",
        "content": "## 引言\n\n这是 **第一段**，包含一个 [链接](https://stepfun.com)。\n\n- 列表项 1\n- 列表项 2\n",
    }
    resp = client.post("/api/v1/formatting/apply", headers=_auth(token), json=payload)
    assert resp.status_code == 200
    body = resp.json()
    html = body["html"]
    assert body["template_id"] == "minimal"
    assert body["title"] == "Step-2 评测"

    # 关键 HTML 片段：应该带 inline style
    assert '<section style=' in html
    assert '<h1 style=' in html  # 标题转 H1
    assert "Step-2 评测" in html
    assert '<h2 style=' in html
    assert '<p style=' in html
    assert '<strong style=' in html
    assert '<ul style=' in html
    assert '<li style=' in html
    assert '<a style=' in html
    assert 'href="https://stepfun.com"' in html


def test_apply_template_unknown_returns_404(client: TestClient) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/formatting/apply",
        headers=_auth(token),
        json={"template_id": "doesnotexist", "content": "x"},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "template_not_found"


def test_apply_template_full_page_wraps_html(client: TestClient) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/formatting/apply",
        headers=_auth(token),
        json={
            "template_id": "business",
            "title": "标题",
            "content": "正文段落",
            "full_page": True,
        },
    )
    assert resp.status_code == 200
    html = resp.json()["html"]
    assert html.startswith("<!doctype html>")
    assert "<title>标题</title>" in html
    assert "<section style=" in html


def test_apply_template_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/formatting/apply",
        json={"template_id": "minimal", "content": "x"},
    )
    assert resp.status_code == 401


def test_apply_template_empty_content_returns_422(client: TestClient) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/formatting/apply",
        headers=_auth(token),
        json={"template_id": "minimal", "content": ""},
    )
    assert resp.status_code == 422
