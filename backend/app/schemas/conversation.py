"""Conversation 与 Message 相关的 Pydantic schema。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConversationMode, MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    mode: ConversationMode = ConversationMode.DIALOGUE


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class MessageCreate(BaseModel):
    role: MessageRole = MessageRole.USER
    content: str = Field(min_length=1)
    audio_url: str | None = Field(default=None, max_length=500)
    referenced_doc_ids: list[str] | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    audio_url: str | None = None
    referenced_doc_ids: list[str] | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    mode: ConversationMode
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class ConversationList(BaseModel):
    items: list[ConversationOut]
    total: int
