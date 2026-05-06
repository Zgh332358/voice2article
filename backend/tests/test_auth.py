"""auth 端到端测试：注册 → 登录 → /me，覆盖 happy path 与主要错误路径。"""

from fastapi.testclient import TestClient


def test_register_login_me_happy_path(client: TestClient) -> None:
    # 1. 注册
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "s3cret-pass", "nickname": "Alice"},
    )
    assert register_resp.status_code == 201, register_resp.text
    body = register_resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["nickname"] == "Alice"
    register_token = body["access_token"]
    assert isinstance(register_token, str) and len(register_token) > 20

    # 2. /me 用注册返回的 token 也应该能用
    me_resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {register_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"

    # 3. 登录
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "s3cret-pass"},
    )
    assert login_resp.status_code == 200, login_resp.text
    login_token = login_resp.json()["access_token"]

    # 4. 用登录 token 再访问 /me
    me_resp2 = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {login_token}"}
    )
    assert me_resp2.status_code == 200
    assert me_resp2.json()["email"] == "alice@example.com"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {"email": "bob@example.com", "password": "another-pass"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    dup = client.post("/api/v1/auth/register", json=payload)
    assert dup.status_code == 409
    assert dup.json()["code"] == "email_exists"


def test_register_password_too_short_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "1234567"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "right-password"},
    )

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


def test_login_nonexistent_email_returns_401(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything-here"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


def test_me_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "missing_token"


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_token"
