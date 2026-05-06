"""Conversation 与 Message 模型 —— 对应 PRD §6.1.3。"""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


# Postgres 用 JSONB；其它方言（SQLite 用于测试）退回到 JSON
JsonType = JSON().with_variant(JSONB, "postgresql")


class ConversationMode(str, enum.Enum):
    DIALOGUE = "dialogue"
    DOCUMENT = "document"
    HYBRID = "hybrid"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mode: Mapped[ConversationMode] = mapped_column(
        Enum(ConversationMode, name="conversation_mode"),
        nullable=False,
        default=ConversationMode.DIALOGUE,
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[UUID] = uuid_pk()
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referenced_doc_ids: Mapped[list[Any] | None] = mapped_column(JsonType, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
