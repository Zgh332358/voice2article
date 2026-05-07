"""Step LLM 客户端封装（OpenAI 兼容 chat.completions）。

支持两种模式：
- complete(): 非流式，整段返回。简单，适合短文本和测试。
- stream(): 流式（SSE），按 chunk 异步迭代 delta.content。生成长文章时降低首屏延迟。
"""

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any, Literal

import httpx
from fastapi import status

from app.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMError(AppError):
    """LLM 上游或本地配置异常。"""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "llm_error"


Role = Literal["system", "user", "assistant"]


class ChatMessage(dict[str, Any]):
    """OpenAI 兼容消息对象。用 dict 而不是 dataclass，方便直接 json.dumps。"""

    def __init__(self, role: Role, content: str) -> None:
        super().__init__(role=role, content=content)


class StepLLMClient:
    """OpenAI 兼容的 Step Chat Completions 调用。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        messages: Sequence[ChatMessage | dict[str, Any]],
        *,
        stream: bool,
        temperature: float,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
            "stream": stream,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

    async def complete(
        self,
        messages: Sequence[ChatMessage | dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """非流式：返回完整 assistant 文本。失败抛 LLMError。"""
        url = f"{self._base_url}/chat/completions"
        payload = self._payload(
            messages, stream=False, temperature=temperature, max_tokens=max_tokens
        )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, headers=self._headers(), json=payload)
        except httpx.RequestError as e:
            logger.error("Step LLM 网络错误: %s", e)
            raise LLMError("LLM 服务不可达", code="llm_unreachable") from e

        if resp.status_code == 401:
            raise LLMError("LLM 凭证失败", code="llm_auth")
        if resp.status_code >= 400:
            logger.warning("Step LLM %s: %s", resp.status_code, resp.text[:300])
            raise LLMError(f"LLM 上游错误（{resp.status_code}）", code="llm_upstream")

        try:
            data = resp.json()
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError) as e:
            logger.error("Step LLM 响应解析失败: %s", resp.text[:300])
            raise LLMError("LLM 响应格式异常", code="llm_bad_response") from e

    async def stream(
        self,
        messages: Sequence[ChatMessage | dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """流式：按 chunk 异步 yield delta.content（已剥 SSE 前缀）。失败抛 LLMError。"""
        url = f"{self._base_url}/chat/completions"
        payload = self._payload(
            messages, stream=True, temperature=temperature, max_tokens=max_tokens
        )

        try:
            # 双层 async with 在 async generator 里语义更稳，不合并
            async with httpx.AsyncClient(timeout=self._timeout) as client:  # noqa: SIM117
                async with client.stream(
                    "POST", url, headers=self._headers(), json=payload
                ) as resp:
                    if resp.status_code == 401:
                        raise LLMError("LLM 凭证失败", code="llm_auth")
                    if resp.status_code >= 400:
                        body = (await resp.aread()).decode("utf-8", errors="replace")
                        logger.warning("Step LLM stream %s: %s", resp.status_code, body[:300])
                        raise LLMError(
                            f"LLM 上游错误（{resp.status_code}）", code="llm_upstream"
                        )

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        payload_str = line[len("data:") :].strip()
                        if payload_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload_str)
                        except json.JSONDecodeError:
                            logger.debug("跳过非 JSON SSE 行: %s", payload_str[:120])
                            continue
                        delta = (
                            chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                        )
                        if delta:
                            yield delta
        except httpx.RequestError as e:
            logger.error("Step LLM 流式网络错误: %r", e)
            raise LLMError("LLM 服务不可达", code="llm_unreachable") from e


def get_llm_client() -> StepLLMClient:
    """从 settings 构造客户端。失败时抛 LLMError 让 FastAPI 走错误信封。"""
    if not settings.step_api_key:
        raise LLMError("STEP_API_KEY 未配置", code="llm_missing_key")
    return StepLLMClient(
        api_key=settings.step_api_key,
        base_url=settings.step_api_base_url,
        model=settings.step_llm_model,
    )
