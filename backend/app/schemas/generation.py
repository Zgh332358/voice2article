"""Generation 相关 Pydantic schema。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import GenerationMode, GenerationStatus
from app.services.prompts import Length, Tone


class GenerationCreate(BaseModel):
    """触发一次生成。当前只支持 mode=dialogue（W3 范围内）。"""

    conversation_id: UUID
    mode: GenerationMode = GenerationMode.DIALOGUE
    tone: Tone = "亲切"
    length: Length = "medium"
    extra_instructions: str | None = Field(default=None, max_length=500)


class GenerationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID | None
    source_mode: GenerationMode
    title: str | None
    generated_content: str | None
    word_count: int | None
    status: GenerationStatus
    created_at: datetime


class GenerationList(BaseModel):
    items: list[GenerationOut]
    total: int
