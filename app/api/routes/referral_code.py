"""модуль маршрутов реферальных кодов.

модуль содержит эндпоинты для создания реферальных кодов и получения реферального кода пользователя по его email.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import APIRouter

from app.crud.referral_code import create_referral_code, delete_referral_code
from app.dependences import AsyncDatabaseSessionDependence, CurrentAuthenticatedUserDependence, RedisDependence
from app.models.referral_code import ReferralCode, ReferralCodeCreate
from app.models.user import UserEmail, UserReferralCode

referrral_code_router: APIRouter = APIRouter()


@referrral_code_router.post(
    "/create",
    summary="создать реферальный код",
    description="""
        создает новый реферальный код для пользователя.\n
        для создания необходим токен авторизации в заголовке и срок действия кода в теле.
    """,
)
async def create_code(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
    code_lifetime: ReferralCodeCreate,
    redis: RedisDependence,
) -> ReferralCode:
    """создает новый реферальный код для пользователя.

    создает реферальный код с указанным сроком действия и сохраняет его в базе данных.

    аргументы:
        user (CurrentAuthenticatedUserDependence): текущий авторизованный пользователь.
        database_session (AsyncDatabaseSessionDependence): асинхронная сессия базы данных.
        code_lifetime (ReferralCodeCreate): срок действия реферального кода.
        redis (RedisDependence): подключение к Redis.

    возвращает:
        ReferralCode: созданный реферальный код.
    """
    return await create_referral_code(user, database_session, code_lifetime, redis)


@referrral_code_router.delete(
    "/delete",
    summary="удалить реферальный код",
    description="""
        удаляет реферальный код для пользователя.\n
        для удаления необходим токен авторизации в заголовке.
    """,
)
async def delete_code(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
    redis: RedisDependence,
) -> str:
    """удаляет реферальный код для пользователя.

    удаляет реферальный код из базы данных и Redis.

    аргументы:
        user (CurrentAuthenticatedUserDependence): текущий авторизованный пользователь.
        database_session (AsyncDatabaseSessionDependence): асинхронная сессия базы данных.
        redis (RedisDependence): подключение к Redis.

    возвращает:
        str: сообщение об успешном удалении.
    """
    return await delete_referral_code(user, database_session, redis)


@referrral_code_router.post(
    "/get_user_referral_code",
    summary="получить реферальный код пользователя",
    description="""
        получает реферальный код для пользователя по его email.\n
        для этого необходимо передать email пользователя в теле запроса.
    """,
)
async def get_user_referral_code_by_referral_email(
    user_email: UserEmail,
    redis: RedisDependence,
) -> UserReferralCode:
    """получает реферальный код пользователя по его email.

    ищет в Redis реферальный код, связанный с переданным email пользователя.

    аргументы:
        user_email (UserEmail): email пользователя, для которого нужно получить реферальный код.
        redis (RedisDependence): подключение к Redis.

    возвращает:
        UserReferralCode: объект, содержащий email пользователя и его реферальный код.
    """
    code = await redis.get(f"referrer:{user_email.email}")

    return UserReferralCode(
        email=user_email.email,
        referral_code=code,
    )
