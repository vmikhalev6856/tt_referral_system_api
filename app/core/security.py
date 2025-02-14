"""модуль для работы с jwt-токенами и паролями.

модуль содержит функции для создания, верификации jwt-токенов, хеширования паролей и их верификации,
а также для работы с redis для проверки отозванных токенов.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader
from jwt import PyJWTError, decode, encode
from passlib.context import CryptContext
from redis.asyncio import Redis

from app.core.config import settings
from app.models.jwt import JWT, JWTPayload


class TokenType(StrEnum):
    """перечисление типов токенов.

    это перечисление определяет два типа токенов: access и refresh.
    """

    ACCESS = "access"
    REFRESH = "refresh"


password_crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_jwt(
    subject_id: UUID,
    token_type: TokenType,
    request: Request,
) -> JWT:
    """создает jwt-токен.

    эта функция создает новый jwt-токен для указанного пользователя с определенным типом токена.

    аргументы:
        subject_id (uuid): идентификатор субъекта (пользователя)
        token_type (tokentype): тип токена (access или refresh)
        request (request): объект запроса для получения user-agent

    возвращает:
        jwt: объект со сгенерированным токеном
    """
    token_subject_user_agent: str | None = request.headers.get("User-Agent")

    token_timedelta: timedelta = (
        settings.ACCESS_TOKEN_TIMEDELTA if token_type == TokenType.ACCESS else settings.REFRESH_TOKEN_TIMEDELTA
    )

    token_expiration_datetime: datetime = datetime.now() + token_timedelta

    jwt_payload: JWTPayload = JWTPayload(
        token_type=token_type,
        token_subject=str(subject_id),
        token_expiration=str(token_expiration_datetime),
        token_subject_user_agent=token_subject_user_agent,
    )

    encoded_jwt: str = encode(jwt_payload.model_dump(), settings.SECRET_KEY, algorithm=settings.SIGNING_ALGORITHM)

    return JWT(token=f"bearer jwt {encoded_jwt}")


async def verify_jwt(
    token: str,
    token_type: TokenType,
    request: Request,
    redis: Redis,
) -> JWTPayload:
    """проверяет валидность jwt-токена.

    эта функция проверяет jwt-токен на предмет его отозвания, истечения срока действия,
    а также соответствие типа токена и user-agent.

    аргументы:
        token (str): jwt-токен
        token_type (tokentype): тип токена (access или refresh)
        request (request): объект запроса для получения user-agent
        redis (redis): экземпляр redis для проверки отозванных токенов

    возвращает:
        jwtpayload: данные из токена

    выбрасывает:
        httpexception: если токен отозван, истек или некорректен
    """
    if await redis.get(f"revoked:bearer jwt {token}"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "token revoked",
        )

    try:
        token_payload: JWTPayload = JWTPayload(
            **decode(
                token,
                settings.SECRET_KEY,
                settings.SIGNING_ALGORITHM,
            ),
        )

    except PyJWTError as jwt_error:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"could not validate token credentials: {jwt_error}",
        ) from jwt_error

    if token_payload.token_type != token_type:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "invalid token type.",
        )

    if datetime.strptime(token_payload.token_expiration, "%Y-%m-%d %H:%M:%S.%f") <= datetime.now():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "token has expired.",
        )

    if token_payload.token_subject_user_agent != request.headers.get("User-Agent"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "invalid token user agent.",
        )

    return token_payload


def verify_password(password: str, hashed_password: str) -> bool:
    """проверяет, совпадает ли пароль с хешированным паролем.

    эта функция проверяет, совпадает ли введенный пароль с хешированным паролем.

    аргументы:
        password (str): введенный пароль
        hashed_password (str): хешированный пароль

    возвращает:
        bool: True, если пароли совпадают, иначе False
    """
    return password_crypt_context.verify(password, hashed_password)


def get_password_hash(password: str) -> str:
    """хеширует пароль.

    эта функция хеширует переданный пароль с использованием bcrypt.

    аргументы:
        password (str): пароль

    возвращает:
        str: хешированный пароль
    """
    return password_crypt_context.hash(password)


authentication_token_header = APIKeyHeader(
    name="authorization",
    scheme_name="bearer jwt",
    description="oauth2 with bearer token",
)
"""заголовок для токена аутентификации.

используется для извлечения bearer токена из заголовков запроса.
"""
