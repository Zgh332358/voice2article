"""Step-Audio ASR 客户端封装。

把 httpx 调用 / 错误归一化 / 配置注入收在一起，让 API 层只关心业务。
"""

from typing import Any

import httpx
from fastapi import status

from app.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class STTError(AppError):
    """STT 上游或本地配置异常。"""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "stt_error"


class StepASRClient:
    """异步调用 Step ASR `/audio/transcriptions` 端点。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    async def transcribe(
        self,
        *,
        audio: bytes,
        filename: str,
        content_type: str = "audio/wav",
    ) -> str:
        """发送音频字节，返回转写文本。失败抛 STTError。"""
        url = f"{self._base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        # httpx 接受混合形态的 tuple，但 mypy 推不出统一类型，显式标 Any
        files: dict[str, Any] = {
            "file": (filename, audio, content_type),
            "model": (None, self._model),
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, headers=headers, files=files)
        except httpx.RequestError as e:
            logger.error("Step ASR 网络错误: %s", e)
            raise STTError("语音识别服务不可达", code="stt_unreachable") from e

        if resp.status_code == 401:
            logger.error("Step ASR 401（key 失效或无 ASR 权限）")
            raise STTError("STT 凭证失败或无 ASR 权限", code="stt_auth")
        if resp.status_code >= 400:
            logger.warning("Step ASR %s: %s", resp.status_code, resp.text[:300])
            raise STTError(
                f"语音识别上游错误（{resp.status_code}）",
                code="stt_upstream",
            )

        try:
            text = resp.json()["text"]
        except (KeyError, ValueError) as e:
            logger.error("Step ASR 响应解析失败: %s", resp.text[:300])
            raise STTError("STT 响应格式异常", code="stt_bad_response") from e

        if not isinstance(text, str):
            raise STTError("STT 响应 text 非字符串", code="stt_bad_response")
        return text


def get_stt_client() -> StepASRClient:
    """从 settings 构造客户端。每次调用都新建 client，httpx 内部会管连接池。"""
    if not settings.step_api_key:
        raise STTError("STEP_API_KEY 未配置", code="stt_missing_key")
    return StepASRClient(
        api_key=settings.step_api_key,
        base_url=settings.step_api_base_url,
        model=settings.step_stt_model,
    )
