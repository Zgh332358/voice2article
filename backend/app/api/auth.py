"""认证路由：注册、登录、获取当前用户信息。"""

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


class EmailAlreadyExists(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "email_exists"


class InvalidCredentials(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_credentials"


def _build_token_response(user: User) -> TokenResponse:
    token = create_access_token(subject=str(user.id))
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
async def register(payload: UserCreate, db: DbSession) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise EmailAlreadyExists("该邮箱已注册")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(payload: UserLogin, db: DbSession) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentials("邮箱或密码错误")
    return _build_token_response(user)


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
async def me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)
