"""модуль зависимостей для аутентификации пользователей.

содержит зависимости для работы с базой данных, redis и проверки токена доступа

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader
from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_database_session
from app.core.redis import get_redis
from app.core.security import TokenType, authentication_token_header, verify_jwt
from app.models.jwt import JWTPayload
from app.models.user import User, UserView

AsyncDatabaseSessionDependence = Annotated[AsyncSession, Depends(get_async_database_session)]

AuthenticateTokenDependence = Annotated[APIKeyHeader, Depends(authentication_token_header)]

RedisDependence = Annotated[Redis, Depends(get_redis)]


async def get_current_authenticated_user(
    token: AuthenticateTokenDependence,
    database_session: AsyncDatabaseSessionDependence,
    request: Request,
    redis: RedisDependence,
) -> UserView:
    """получает текущего аутентифицированного пользователя по токену доступа.

    Args:
        token: заголовок с токеном авторизации.
        database_session: асинхронная сессия базы данных.
        request: объект запроса fastapi.
        redis: клиент redis для проверки токена.

    Returns:
        userview: объект пользователя с обновленными данными.

    """
    token_payload: JWTPayload = await verify_jwt(token[11:], TokenType.ACCESS, request, redis)

    user: User = await database_session.scalar(
        select(User).options(selectinload(User.referral_code)).where(User.id == token_payload.token_subject),
    )

    if not user.referral_code:
        return UserView.model_validate(user, update={"referral_code": None})

    return UserView.model_validate(user)


CurrentAuthenticatedUserDependence = Annotated[UserView, Depends(get_current_authenticated_user)]
