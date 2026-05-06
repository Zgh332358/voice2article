"""Generation 模型 —— 对应 PRD §6.1.4。"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.conversation import JsonType

if TYPE_CHECKING:
    from app.models.user import User


class GenerationMode(StrEnum):
    DIALOGUE = "dialogue"
    DOCUMENT = "document"
    HYBRID = "hybrid"


class GenerationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DELETED = "deleted"


class Generation(Base, TimestampMixin):
    __tablename__ = "generations"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_mode: Mapped[GenerationMode] = mapped_column(
        Enum(GenerationMode, name="generation_mode"),
        nullable=False,
    )
    source_data: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style_profile: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status"),
        nullable=False,
        default=GenerationStatus.DRAFT,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="generations")
