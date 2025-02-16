"""модуль инициализации fastapi-приложения.

содержит настройку приложения, подключение маршрутов и управление жизненным циклом приложения

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.main import api_router
from app.core.config import settings
from app.core.redis import get_redis
from app.core.utils import inform_host


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """управляет жизненным циклом приложения.

    выполняет инициализацию redis при запуске и закрывает соединение при завершении работы
    """
    redis = await get_redis()
    await inform_host("app started with active redis connection, waiting for requests")

    yield

    await redis.close()
    await inform_host("app stopped, redis connection closed")


app: FastAPI = FastAPI(
    title=settings.PROJECT_NAME,
    summary=settings.PROJECT_SUMMARY,
    description=settings.PROJECT_DESCRIPTION,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "showExtensions": True,
    },
    lifespan=lifespan,
)

app.include_router(api_router)


def custom_openapi() -> dict:
    """кастомизирует openapi-схему приложения.

    удаляет описание кода ответа 422 (ошибка валидации) из всех эндпоинтов

    Returns:
        dict: openapi-схема приложения

    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        summary=app.summary,
        description=app.description,
        version=app.version,
        routes=app.routes,
    )

    http_methods = ["post", "get", "put", "delete"]

    for method in openapi_schema["paths"]:
        for m in http_methods:
            with contextlib.suppress(KeyError):
                del openapi_schema["paths"][method][m]["responses"]["422"]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi
