"""Generation 端点：基于会话历史 → Prompt → Step LLM → 持久化。

提供两个端点：
- POST /generations         同步，返回完整 GenerationOut
- POST /generations/stream  流式 SSE：每个 token 一个 event；最终发 done event
"""

import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models import (
    Conversation,
    Generation,
    GenerationMode,
    GenerationStatus,
    MessageRole,
)
from app.schemas import GenerationCreate, GenerationList, GenerationOut
from app.services.llm import LLMError, StepLLMClient, get_llm_client
from app.services.prompts import build_dialogue_generation_messages, split_title_and_body

router = APIRouter(prefix="/generations", tags=["generations"])
logger = get_logger(__name__)

LlmClientDep = Annotated[StepLLMClient, Depends(get_llm_client)]


class ConversationNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "conversation_not_found"


class EmptyConversationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "empty_conversation"


async def _load_user_messages(
    db: DbSession, conv_id: UUID, user_id: UUID
) -> tuple[Conversation, list[str]]:
    """拿到一个会话以及它的全部 user 消息文本，按时间正序。"""
    conv = await db.scalar(
        select(Conversation)
        .where(Conversation.id == conv_id)
        .options(selectinload(Conversation.messages))
    )
    if conv is None or conv.user_id != user_id:
        raise ConversationNotFoundError("会话不存在")

    user_msgs = [m.content for m in conv.messages if m.role == MessageRole.USER]
    if not user_msgs:
        raise EmptyConversationError("会话里还没有用户消息可以用来生成")
    return conv, user_msgs


async def _persist_generation(
    db: DbSession,
    *,
    user_id: UUID,
    conversation_id: UUID,
    mode: GenerationMode,
    title: str | None,
    content: str,
    source_data: dict[str, object],
) -> Generation:
    gen = Generation(
        user_id=user_id,
        conversation_id=conversation_id,
        source_mode=mode,
        source_data=source_data,
        title=title,
        generated_content=content,
        word_count=len(content),
        status=GenerationStatus.DRAFT,
    )
    db.add(gen)
    await db.commit()
    await db.refresh(gen)
    return gen


@router.post(
    "",
    response_model=GenerationOut,
    status_code=status.HTTP_201_CREATED,
    summary="生成文章（同步，等完整结果）",
)
async def create_generation(
    payload: GenerationCreate,
    current_user: CurrentUser,
    db: DbSession,
    llm: LlmClientDep,
) -> GenerationOut:
    if payload.mode != GenerationMode.DIALOGUE:
        raise EmptyConversationError("当前 MVP 只支持 mode=dialogue（W3 范围）")

    _, user_msgs = await _load_user_messages(db, payload.conversation_id, current_user.id)
    messages = build_dialogue_generation_messages(
        user_messages=user_msgs,
        tone=payload.tone,
        length=payload.length,
        extra_instructions=payload.extra_instructions,
    )

    raw = await llm.complete(messages)
    title, body = split_title_and_body(raw)

    gen = await _persist_generation(
        db,
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        mode=GenerationMode.DIALOGUE,
        title=title or None,
        content=body or raw,
        source_data={
            "tone": payload.tone,
            "length": payload.length,
            "user_message_count": len(user_msgs),
            "model": llm.model,
        },
    )
    logger.info(
        "user=%s gen=%s words=%s model=%s",
        current_user.id, gen.id, gen.word_count, llm.model,
    )
    return GenerationOut.model_validate(gen)


@router.post(
    "/stream",
    summary="生成文章（流式 SSE，边算边推）",
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def create_generation_stream(
    payload: GenerationCreate,
    current_user: CurrentUser,
    db: DbSession,
    llm: LlmClientDep,
) -> StreamingResponse:
    if payload.mode != GenerationMode.DIALOGUE:
        raise EmptyConversationError("当前 MVP 只支持 mode=dialogue（W3 范围）")

    _, user_msgs = await _load_user_messages(db, payload.conversation_id, current_user.id)
    messages = build_dialogue_generation_messages(
        user_messages=user_msgs,
        tone=payload.tone,
        length=payload.length,
        extra_instructions=payload.extra_instructions,
    )

    async def event_source() -> AsyncIterator[bytes]:
        chunks: list[str] = []
        try:
            async for delta in llm.stream(messages):
                chunks.append(delta)
                event = {"type": "delta", "content": delta}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
        except LLMError as e:
            err = {"type": "error", "code": e.code, "detail": e.detail}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode()
            return

        full = "".join(chunks)
        title, body = split_title_and_body(full)
        gen = await _persist_generation(
            db,
            user_id=current_user.id,
            conversation_id=payload.conversation_id,
            mode=GenerationMode.DIALOGUE,
            title=title or None,
            content=body or full,
            source_data={
                "tone": payload.tone,
                "length": payload.length,
                "user_message_count": len(user_msgs),
                "model": llm.model,
                "streamed": True,
            },
        )
        done = {
            "type": "done",
            "generation_id": str(gen.id),
            "title": gen.title,
            "word_count": gen.word_count,
        }
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n".encode()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁 nginx 缓冲
        },
    )


@router.get("", response_model=GenerationList, summary="列出当前用户的生成历史")
async def list_generations(
    current_user: CurrentUser,
    db: DbSession,
    conversation_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> GenerationList:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    where = [Generation.user_id == current_user.id]
    if conversation_id is not None:
        where.append(Generation.conversation_id == conversation_id)

    total = await db.scalar(
        select(func.count(Generation.id)).where(*where)
    )
    rows = await db.scalars(
        select(Generation).where(*where).order_by(Generation.created_at.desc())
        .limit(limit).offset(offset)
    )
    return GenerationList(
        items=[GenerationOut.model_validate(g) for g in rows],
        total=int(total or 0),
    )


@router.get("/{gen_id}", response_model=GenerationOut, summary="获取一次生成的详情")
async def get_generation(
    gen_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> GenerationOut:
    gen = await db.get(Generation, gen_id)
    if gen is None or gen.user_id != current_user.id:
        raise ConversationNotFoundError("生成记录不存在")
    return GenerationOut.model_validate(gen)
