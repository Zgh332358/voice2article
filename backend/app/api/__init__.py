"""API 路由：所有路由汇集到 api_router 后挂载到 /api/v1。"""

from fastapi import APIRouter

from app.api import auth, conversations, formatting, generations, health, metrics, stt

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(stt.router)
api_router.include_router(conversations.router)
api_router.include_router(generations.router)
api_router.include_router(formatting.router)
