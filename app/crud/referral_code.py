"""модуль для создания и управления реферальными кодами.

в этом модуле находится логика для создания реферальных кодов для пользователей.
он генерирует код, сохраняет его в базе данных и кэширует в redis с указанным временем жизни.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

import secrets
import string
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import ReferralCode
from app.models.referral_code import ReferralCodeCreate
from app.models.user import UserView


async def create_referral_code(
    user: UserView,
    database_session: AsyncSession,
    code_lifetime: ReferralCodeCreate,
    redis: Redis,
) -> ReferralCode:
    """создает новый реферальный код для пользователя.

    сохраняет его в базе данных и кэширует в redis с заданным временем истечения срока.

    Args:
        user (userview): пользователь, для которого создается реферальный код
        database_session (asyncsession): асинхронная сессия для работы с базой данных
        code_lifetime (referralcodecreate): время жизни реферального кода в часах
        redis (redis): экземпляр redis для кэширования.

    Returns:
        referralcode: созданный реферальный код

    Raises:
        HTTPException: сообщение об ошибке при создании кода

    """
    redis_key: str = f"referrer:{user.email}"

    if await redis.get(redis_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="код уже существует",
        )

    existing_code = await database_session.scalar(select(ReferralCode).where(ReferralCode.user_id == user.id))

    if existing_code:
        await database_session.delete(existing_code)
        await database_session.commit()

    code_characters = string.ascii_letters + string.digits
    code = "".join(secrets.choice(code_characters) for _ in range(16))

    new_code = ReferralCode(
        code=code,
        code_expiration=(datetime.now() + timedelta(hours=code_lifetime.lifetime_in_hours)),
        user_id=user.id,
    )

    try:
        database_session.add(new_code)
        await database_session.commit()
        await database_session.refresh(new_code)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="в базе уже существует сущность или неверно указаны типы",
        ) from error

    await redis.setex(f"referrer:{user.email}", code_lifetime.lifetime_in_hours * 3600, code)

    return new_code


async def delete_referral_code(
    user: UserView,
    database_session: AsyncSession,
    redis: Redis,
) -> str:
    """удаляет реферальный код для пользователя из базы данных и Redis.

    Args:
        user (UserView): пользователь, для которого удаляется реферальный код
        database_session (AsyncSession): сессия для работы с базой данных
        redis (Redis): экземпляр Redis для удаления кэша

    Raises:
        HTTPException: сообщение об успешном удалении.

    """
    redis_key: str = f"referrer:{user.email}"

    if await redis.get(redis_key):
        await redis.delete(redis_key)
        existing_code = await database_session.scalar(select(ReferralCode).where(ReferralCode.user_id == user.id))
        await database_session.delete(existing_code)
        await database_session.commit()

        raise HTTPException(status.HTTP_200_OK, "реферальный код успешно удален")

    raise HTTPException(status.HTTP_404_NOT_FOUND, "нет активного реферального кода")
