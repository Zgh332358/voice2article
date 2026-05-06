"""STT 端点端到端测试 —— 通过 dependency override 注入假的 ASR client，不打 Step API。"""

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.stt import StepASRClient, STTError, get_stt_client


def _register(client: TestClient, email: str = "stt@aiken.dev") -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "passw0rd1", "nickname": "STT Tester"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def fake_stt() -> AsyncMock:
    """注入假的 STT client，返回固定文本，捕获参数供断言。"""
    fake = AsyncMock(spec=StepASRClient)
    fake.model = "step-asr-test"
    fake.transcribe.return_value = "你好，阶跃星辰。"
    app.dependency_overrides[get_stt_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_stt_client, None)


def _audio_field(payload: bytes = b"RIFF\x00\x00\x00\x00WAVE", *, name: str = "audio.wav",
                 mime: str = "audio/wav") -> dict[str, Any]:
    return {"file": (name, payload, mime)}


def test_transcribe_happy_path(client: TestClient, fake_stt: AsyncMock) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files=_audio_field(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["text"] == "你好，阶跃星辰。"
    assert body["model"] == "step-asr-test"
    assert body["audio_bytes"] > 0

    fake_stt.transcribe.assert_awaited_once()
    kwargs = fake_stt.transcribe.await_args.kwargs
    assert kwargs["filename"] == "audio.wav"
    assert kwargs["content_type"] == "audio/wav"


def test_transcribe_requires_auth(client: TestClient, fake_stt: AsyncMock) -> None:
    resp = client.post("/api/v1/stt/transcribe", files=_audio_field())
    assert resp.status_code == 401
    fake_stt.transcribe.assert_not_called()


def test_transcribe_rejects_unsupported_mime(client: TestClient, fake_stt: AsyncMock) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files=_audio_field(name="notes.txt", mime="text/plain"),
    )
    assert resp.status_code == 415
    assert resp.json()["code"] == "unsupported_audio"
    fake_stt.transcribe.assert_not_called()


def test_transcribe_rejects_empty_file(client: TestClient, fake_stt: AsyncMock) -> None:
    token = _register(client)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files=_audio_field(payload=b""),
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "empty_audio"
    fake_stt.transcribe.assert_not_called()


def test_transcribe_rejects_oversized_file(
    client: TestClient, fake_stt: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.stt.MAX_AUDIO_BYTES", 16)
    token = _register(client)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files=_audio_field(payload=b"a" * 100),
    )
    assert resp.status_code == 413
    assert resp.json()["code"] == "file_too_large"
    fake_stt.transcribe.assert_not_called()


def test_transcribe_propagates_upstream_failure(
    client: TestClient, fake_stt: AsyncMock
) -> None:
    fake_stt.transcribe.side_effect = STTError("上游 5xx", code="stt_upstream")
    token = _register(client)
    resp = client.post(
        "/api/v1/stt/transcribe",
        headers={"Authorization": f"Bearer {token}"},
        files=_audio_field(),
    )
    assert resp.status_code == 502
    assert resp.json()["code"] == "stt_upstream"
