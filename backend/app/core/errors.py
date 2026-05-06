"""统一的异常 / 错误响应。

错误响应 schema 约定（与前端对齐）：
    {"detail": "<人类可读>", "code": "<可选机器码>"}
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """业务侧异常基类。子类化以表达不同领域的错误。"""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(self, detail: str, *, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code


def _envelope(detail: str, code: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"detail": detail}
    if code:
        body["code"] = code
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError: %s (%s)", exc.detail, exc.code)
        return JSONResponse(status_code=exc.status_code, content=_envelope(exc.detail, exc.code))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_envelope(str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope("请求参数校验失败", code="validation_error")
            | {"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("服务器内部错误", code="internal_error"),
        )
