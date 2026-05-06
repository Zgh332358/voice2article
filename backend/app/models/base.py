"""ORM 基类与公共 Mixin。

- Base: SQLAlchemy 2.0 typed DeclarativeBase
- TimestampMixin: 自动维护 created_at / updated_at
- uuid_pk: 通用 UUID 主键工厂
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def uuid_pk() -> Mapped[UUID]:
    """统一的 UUID 主键列工厂。"""
    return mapped_column(primary_key=True, default=uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
    )
