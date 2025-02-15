"""модуль маршрутов реферальных кодов.

модуль содержит эндпоинты для создания реферальных кодов и получения реферального кода пользователя по его email.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import APIRouter

from app.crud.referral_code import create_referral_code, delete_referral_code
from app.dependences import AsyncDatabaseSessionDependence, CurrentAuthenticatedUserDependence, RedisDependence
from app.models.referral_code import ReferralCode, ReferralCodeByEmail, ReferralCodeCreate
from app.models.user import UserEmail

referrral_code_router: APIRouter = APIRouter()


@referrral_code_router.post(
    "/create",
    summary="создать реферальный код",
    description="""
        создает новый реферальный код для пользователя.\n
        для создания необходим токен авторизации в заголовке и срок действия кода в теле запроса.
        срок передается целым неотрицательным количеством часов
    """,
)
async def create_code(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
    code_lifetime: ReferralCodeCreate,
    redis: RedisDependence,
) -> ReferralCode:
    """создает новый реферальный код тещего аутентифицированного пользователя.

    создает реферальный код с указанным сроком действия и сохраняет его в базе данных.
    бессрочный код создать нельзя

    Args:
        user (CurrentAuthenticatedUserDependence): зависимость, обеспечивающая аутентификацию пользователя
            по заголовку с токеном
        database_session (AsyncDatabaseSessionDependence): зависимость, обеспечивающая активное
            асинхронное соединение с базой данных
        code_lifetime (ReferralCodeCreate): объект, содержащий срок действия реферального кода
        redis (RedisDependence): зависимость, обеспечивающая активное подключение к redis

    Returns:
        ReferralCode: созданный реферальный код.

    """
    return await create_referral_code(user, database_session, code_lifetime, redis)


@referrral_code_router.delete(
    "/delete",
    summary="удалить реферальный код",
    description="""
        удаляет реферальный код для пользователя.\n
        для удаления необходим токен авторизации в заголовке запроса
    """,
)
async def delete_code(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
    redis: RedisDependence,
) -> str:
    """удаляет реферальный код аутентифицированного пользователя.

    удаляет реферальный код из базы данных и redis

    Args:
        user (CurrentAuthenticatedUserDependence): зависимость, обеспечивающая аутентификацию пользователя
            по заголовку с токеном
        database_session (AsyncDatabaseSessionDependence): зависимость, обеспечивающая активное
            асинхронное соединение с базой данных
        redis (RedisDependence): зависимость, обеспечивающая активное подключение к redis

    Returns:
        str: сообщение об успешном удалении

    """
    return await delete_referral_code(user, database_session, redis)


@referrral_code_router.post(
    "/get_user_referral_code",
    summary="получить реферальный код пользователя",
    description="""
        получает реферальный код для пользователя по его email.\n
        для этого необходимо передать email пользователя в теле запроса.
        эндпоинт открыт для неаутентифицированных пользователей,
        поэтому регистрация пользователя в системе неважна для избежания избыточной информации в ответе
    """,
)
async def get_user_referral_code_by_referral_email(
    user_email: UserEmail,
    redis: RedisDependence,
) -> ReferralCodeByEmail:
    """получает реферальный код пользователя по его email.

    ищет в redis реферальный код, связанный с переданным email пользователя.
    так как эндпоинт открыт для неаутентифицированных пользователей,
    его реализация не возвращает никакой избыточной информации
    (например, если пользователь в системе не зарегистриван,
    мы получим такой же ответ, как если бы у зарегистрированного пользователя не было активного кода)

    Args:
        user_email (UserEmail): email пользователя, для которого нужно получить реферальный код
        redis (RedisDependence): зависимость, обеспечивающая активное подключение к redis

    Returns:
        UserReferralCode: объект, содержащий email пользователя и его реферальный код

    """
    code = await redis.get(f"referrer:{user_email.email}")

    return ReferralCodeByEmail(
        email=user_email.email,
        referral_code=code,
    )
