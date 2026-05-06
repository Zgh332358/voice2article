"""健康检查端点。"""

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    name: str
    version: str
    env: str


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        name=settings.app_name,
        version=__version__,
        env=settings.app_env,
    )
