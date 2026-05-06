"""FastAPI 共享依赖：DB session、当前用户。"""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_token
from app.db import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "auth_error"


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError("缺少 Authorization Bearer", code="missing_token")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as e:
        raise AuthError("token 已过期", code="token_expired") from e
    except jwt.PyJWTError as e:
        raise AuthError("token 无效", code="invalid_token") from e

    sub = payload.get("sub")
    if not sub:
        raise AuthError("token 缺 sub", code="invalid_token")

    try:
        user_id = UUID(sub)
    except ValueError as e:
        raise AuthError("token sub 非合法 UUID", code="invalid_token") from e

    user = await db.get(User, user_id)
    if user is None:
        raise AuthError("用户不存在", code="user_not_found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
