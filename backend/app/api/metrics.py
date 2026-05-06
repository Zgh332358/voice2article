"""metrics 端点：暴露应用运行状态。

当前为最简实现 —— 进程级内存计数，重启后归零。
生产化时可换 prometheus_client。
"""

import sys
import time
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.config import settings

router = APIRouter()

_started_at = time.monotonic()
_started_at_wall = datetime.now(UTC)
_request_count = 0


def increment_request_count() -> None:
    global _request_count
    _request_count += 1


class MetricsResponse(BaseModel):
    name: str
    version: str
    env: str
    uptime_seconds: float
    started_at: datetime
    request_count: int
    python_version: str


@router.get("/metrics", response_model=MetricsResponse, summary="进程指标")
async def metrics() -> MetricsResponse:
    return MetricsResponse(
        name=settings.app_name,
        version=__version__,
        env=settings.app_env,
        uptime_seconds=round(time.monotonic() - _started_at, 3),
        started_at=_started_at_wall,
        request_count=_request_count,
        python_version=sys.version.split()[0],
    )
