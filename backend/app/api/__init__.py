"""API 路由：所有路由汇集到 api_router 后挂载到 /api/v1。"""

from fastapi import APIRouter

from app.api import auth, health, metrics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["health"])
api_router.include_router(auth.router)
