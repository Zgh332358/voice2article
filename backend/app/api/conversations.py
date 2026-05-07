"""Conversations CRUD + 追加消息端点。

权限模型：所有端点都要求登录，且只能操作自己拥有的会话。
"""

from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationList,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "conversation_not_found"


async def _get_owned(db: DbSession, conv_id: UUID, user_id: UUID) -> Conversation:
    """取一个会话并校验属主，否则统一返回 404（不暴露存在性）。"""
    conv = await db.get(Conversation, conv_id)
    if conv is None or conv.user_id != user_id:
        raise ConversationNotFoundError("会话不存在")
    return conv


@router.post(
    "",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建会话",
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationOut:
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title,
        mode=payload.mode,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationOut.model_validate(conv)


@router.get("", response_model=ConversationList, summary="获取当前用户的会话列表")
async def list_conversations(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> ConversationList:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    total = await db.scalar(
        select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    )
    rows = await db.scalars(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return ConversationList(
        items=[ConversationOut.model_validate(c) for c in rows],
        total=int(total or 0),
    )


@router.get("/{conv_id}", response_model=ConversationDetail, summary="获取会话详情（含消息）")
async def get_conversation(
    conv_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationDetail:
    conv = await db.scalar(
        select(Conversation)
        .where(Conversation.id == conv_id)
        .options(selectinload(Conversation.messages))
    )
    if conv is None or conv.user_id != current_user.id:
        raise ConversationNotFoundError("会话不存在")
    return ConversationDetail.model_validate(conv)


@router.patch("/{conv_id}", response_model=ConversationOut, summary="更新会话标题")
async def update_conversation(
    conv_id: UUID,
    payload: ConversationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationOut:
    conv = await _get_owned(db, conv_id, current_user.id)
    if payload.title is not None:
        conv.title = payload.title
    await db.commit()
    await db.refresh(conv)
    return ConversationOut.model_validate(conv)


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除会话")
async def delete_conversation(
    conv_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    conv = await _get_owned(db, conv_id, current_user.id)
    await db.delete(conv)
    await db.commit()


@router.post(
    "/{conv_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
    summary="向会话追加消息",
)
async def append_message(
    conv_id: UUID,
    payload: MessageCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageOut:
    conv = await _get_owned(db, conv_id, current_user.id)
    msg = Message(
        conversation_id=conv.id,
        role=payload.role,
        content=payload.content,
        audio_url=payload.audio_url,
        referenced_doc_ids=payload.referenced_doc_ids,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageOut.model_validate(msg)
