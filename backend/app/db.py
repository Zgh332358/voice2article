"""异步数据库引擎与会话工厂。

- 引擎在应用生命周期内单例
- 每次请求通过 get_db 依赖获得一个 AsyncSession，请求结束自动关闭
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _build_engine_kwargs() -> dict:
    kwargs: dict = {"echo": False, "pool_pre_ping": True}
    # SQLite 不支持连接池配置项，按 URL 区分
    if settings.database_url.startswith("sqlite"):
        kwargs["echo"] = False
    return kwargs


engine = create_async_engine(settings.database_url, **_build_engine_kwargs())

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：每个请求一个 AsyncSession。"""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
