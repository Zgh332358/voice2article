"""Pydantic schema —— 请求 / 响应模型，与 ORM 解耦。"""

from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationList,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)
from app.schemas.formatting import FormatRequest, FormatResponse, TemplateInfo, TemplateList
from app.schemas.generation import GenerationCreate, GenerationList, GenerationOut
from app.schemas.stt import TranscribeResponse
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserOut

__all__ = [
    "ConversationCreate",
    "ConversationDetail",
    "ConversationList",
    "ConversationOut",
    "ConversationUpdate",
    "FormatRequest",
    "FormatResponse",
    "GenerationCreate",
    "GenerationList",
    "GenerationOut",
    "MessageCreate",
    "MessageOut",
    "TemplateInfo",
    "TemplateList",
    "TokenResponse",
    "TranscribeResponse",
    "UserCreate",
    "UserLogin",
    "UserOut",
]
