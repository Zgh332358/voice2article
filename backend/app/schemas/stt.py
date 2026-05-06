"""STT 相关 Pydantic schema。"""

from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    text: str = Field(description="转写文本")
    model: str = Field(description="使用的 STT 模型")
    audio_bytes: int = Field(description="原始音频字节数")
