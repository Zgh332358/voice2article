"""安全工具：密码哈希 + JWT 编解码。

- 密码：bcrypt（cost=12，OWASP 当前推荐档）
- JWT：HS256，过期默认 7 天（settings.jwt_expire_minutes）
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.config import settings


def hash_password(plain: str) -> str:
    """生成 bcrypt 哈希。返回的字符串已含 salt 与 cost。"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, *, extra: dict[str, Any] | None = None) -> str:
    """生成 access token。subject 通常是 user_id 字符串。"""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验 token。失败抛 jwt.PyJWTError 子类。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
