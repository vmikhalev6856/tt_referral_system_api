"""модуль маршрутов для пользователей.

модуль содержит эндпоинты для регистрации, авторизации, получения реферальных кодов и управления токенами пользователей.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import APIRouter, HTTPException, Request

from app.core.security import TokenType, create_jwt, verify_jwt
from app.core.utils import get_available_verifications_count
from app.crud.user import authenticate_user, create_user, get_user_refferals
from app.dependences import AsyncDatabaseSessionDependence, CurrentAuthenticatedUserDependence, RedisDependence
from app.models.jwt import JWTsPair
from app.models.user import LoginUser, RefreshLoginUser, RegisterUser, UserReferrals, UserRegistrationsAvailableCount, UserView

user_router: APIRouter = APIRouter()


@user_router.get(
    "/registrations_available_count",
    summary="получить количество доступных регистраций",
    description="""
        возвращает количество доступных регистраций пользователей.\n
        предоставляет пару токенов: токен авторизации и токен обновления.\n
        после того как токен авторизации истечет, новая пара будет выдана с использованием токена обновления.
    """,
)
async def get_registrations_available_count() -> UserRegistrationsAvailableCount:
    """получает количество доступных регистраций пользователей.

    возвращает количество доступных регистраций

    Returns:
        UserRegistrationsAvailableCount: объект, содержащий количество доступных регистраций

    """
    registrations_available_count = await get_available_verifications_count()

    return UserRegistrationsAvailableCount(registrations_available_count=registrations_available_count)


@user_router.post(
    "/registration",
    summary="зарегистрировать нового пользователя",
    description="""
        регистрирует нового пользователя.\n
        для этого нужно указать email, пароль и (необязательно) реферальный код реферала.
        если реферальный код не используется для регистрации, поле нужно заполнить значение null без ковычек.
        регистрация доступна даже аутентифицированным пользователям.
    """,
)
async def register_user(
    user: RegisterUser,
    database_session: AsyncDatabaseSessionDependence,
) -> UserView:
    """регистрирует нового пользователя и возвращает информацию о созданном пользователя в случае успеха.

    Args:
        user (RegisterUser): объект с информацией для регистрации (email, password, referral_code (опционально))
        database_session (AsyncDatabaseSessionDependence): зависимость, обеспечивающая наличие активной сессии с базой данных
            для сохранения нового пользователя

    Returns:
        UserView: объект с информацией о зарегистрированном пользователе

    """
    return await create_user(user, database_session)


@user_router.post(
    "/login",
    summary="аутентифицировать пользователя и вернуть токены",
    description="""
        аутентифицирует пользователя по email и паролю.\n
        если аутентификация успешна, возвращает пару токенов: токен доступа и токен обновления.\n
        токен доступа используется для аутентификации, и когда он истечет,\n
        новая пара токенов может быть выдана с использованием токена обновления.\n
        после получения ответа с парой токенов, скопируйте токен доступа\n
        и вставьте его в форму авторизации для доступа к защищенным эндпоинтам.
    """,
)
async def login_user(
    user: LoginUser,
    database_session: AsyncDatabaseSessionDependence,
    request: Request,
) -> JWTsPair:
    """аутентифицирует пользователя и возвращает токены доступа и обновления.

    Args:
        user (LoginUser): данные для аутентификации (email и пароль).
        database_session (AsyncDatabaseSessionDependence): зависимость, обеспечивающая наличие активной сессии с базой данных
        request (Request): объект запроса для выдачи более безопасных токенов

    Returns:
        JWTsPair: пару токенов jwt (доступа и обновления)

    """
    authenticated_user = await authenticate_user(
        user,
        database_session,
    )

    return JWTsPair(
        access_token=create_jwt(authenticated_user.id, TokenType.ACCESS, request),
        refresh_token=create_jwt(authenticated_user.id, TokenType.REFRESH, request),
    )


@user_router.post(
    "/refresh_login",
    summary="обновить токены пользователя",
    description="""
        обновляет токены пользователя с использованием токена обновления.\n
        возвращает пару токенов: токен доступа и токен обновления.\n
        токен доступа используется для аутентификации, и когда он истечет,\n
        новая пара может быть выдана с использованием токена обновления.\n
        после получения ответа с парой токенов, скопируйте токен доступа\n
        и вставьте его в форму авторизации для доступа к защищенным эндпоинтам
    """,
)
async def refresh_login_user(
    token: RefreshLoginUser,
    redis: RedisDependence,
    request: Request,
) -> JWTsPair:
    """обновляет токены пользователя с использованием токена обновления.

    Args:
        token (RefreshLoginUser): токен обновления
        redis (RedisDependence): зависимость от Redis
        request (Request): объект запроса для извлечения данных клиента

    Returns:
        JWTsPair: пару токенов jwt (доступа и обновления)

    """
    redis_key = f"revoked:{token.refresh_token}"

    jwt_payload = await verify_jwt(token.refresh_token, TokenType.REFRESH, request, redis)

    await redis.setex(redis_key, 3 * 24 * 3600, token.refresh_token)

    return JWTsPair(
        access_token=create_jwt(jwt_payload.token_subject, TokenType.ACCESS, request),
        refresh_token=create_jwt(jwt_payload.token_subject, TokenType.REFRESH, request),
    )


@user_router.get(
    "/logout",
    summary="выход из системы",
    description="""
        аннулирует текущий токен доступа пользователя, добавляя его в список отозванных.\n
        при этом токен обновления остаётся действительным.
    """,
)
async def logout_user(
    _: CurrentAuthenticatedUserDependence,
    redis: RedisDependence,
    request: Request,
) -> None:
    """аннулирует текущий токен доступа пользователя.

    добавляет токен в список отозванных в redis

    Raises:
        HTTPException: возвращает 200 с сообщением об успешном выходе из системы

    """
    redis_key = f"revoked:{request.headers.get('authorization')}"
    await redis.setex(redis_key, 60 * 60, request.headers.get("authorization"))

    raise HTTPException(200, detail="выход из системы, токен авторизации аннулирован")


@user_router.get(
    "/referrals",
    summary="получить информацию о пользователе и список его рефералов",
    description="""
        возвращает информацию о пользователе и  список рефералов.\n
        для этого пользователь должен быть авторизован
    """,
)
async def get_user_referrals(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
) -> UserReferrals:
    """возвращает информацию о пользователе и  список рефералов.

    Args:
        user (CurrentAuthenticatedUserDependence): зависимость, обеспечивающая наличие авторизованного пользователя
        database_session (AsyncDatabaseSessionDependence): зависимость, обеспечивающая наличие активной сессии с базой данных

    Returns:
        UserReferrals: информация о пользователе и список рефералов

    """
    return await get_user_refferals(user, database_session)
