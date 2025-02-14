"""модуль маршрутов для пользователей.

модуль содержит эндпоинты для регистрации, авторизации, получения реферальных кодов и управления токенами пользователей.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

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

    возвращает количество доступных регистраций.

    возвращает:
        UserRegistrationsAvailableCount: объект, содержащий количество доступных регистраций.
    """
    registrations_available_count = await get_available_verifications_count()

    return UserRegistrationsAvailableCount(registrations_available_count=registrations_available_count)


@user_router.post(
    "/registration",
    summary="зарегистрировать нового пользователя",
    description="""
        регистрирует нового пользователя.\n
        для этого нужно указать email, пароль и (необязательно) реферальный код реферала.
    """,
)
async def register_user(
    user: RegisterUser,
    database_session: AsyncDatabaseSessionDependence,
) -> UserView:
    """регистрирует нового пользователя и возвращает токены доступа и обновления.

    аргументы:
        user: данные для регистрации пользователя.
        database_session: асинхронная сессия базы данных.

    возвращает:
        UserView: представление зарегистрированного пользователя.
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

    аргументы:
        user: данные для аутентификации (email и пароль).
        database_session: асинхронная сессия базы данных.
        request: объект запроса для извлечения данных клиента.

    возвращает:
        JWTsPair: пару токенов jwt (доступа и обновления).

    исключения:
        HTTPException: если аутентификация не удалась из-за неверных учетных данных.
    """
    authenticated_user: UserView | None = await authenticate_user(
        user,
        database_session,
    )

    if not authenticate_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid email or password",
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
        и вставьте его в форму авторизации для доступа к защищенным эндпоинтам.
    """,
)
async def refresh_login_user(
    token: RefreshLoginUser,
    redis: RedisDependence,
    request: Request,
) -> JWTsPair:
    """обновляет токены пользователя с использованием токена обновления.

    аргументы:
        token: токен обновления.
        redis: зависимость от Redis.
        request: объект запроса для извлечения данных клиента.

    возвращает:
        JWTsPair: пару токенов jwt (доступа и обновления).
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
) -> JSONResponse:
    """аннулирует текущий токен доступа пользователя.

    добавляет токен в список отозванных в Redis.

    возвращает:
        JSONResponse: подтверждение аннулирования токена.
    """
    redis_key = f"revoked:{request.headers.get('authorization')}"
    await redis.setex(redis_key, 15 * 60, request.headers.get("authorization"))

    return JSONResponse(
        {"success": f"revoked {request.headers.get('authorization')}"},
        200,
    )


@user_router.get(
    "/referrals",
    summary="получить информацию о рефералах",
    description="""
        возвращает список рефералов.\n
        для этого пользователь должен быть авторизован.
    """,
)
async def get_user_referrals(
    user: CurrentAuthenticatedUserDependence,
    database_session: AsyncDatabaseSessionDependence,
) -> UserReferrals:
    """возвращает список рефералов пользователя.

    аргументы:
        user: текущий авторизованный пользователь.
        database_session: асинхронная сессия базы данных.

    возвращает:
        UserReferrals: список рефералов пользователя.
    """
    return await get_user_refferals(user, database_session)
