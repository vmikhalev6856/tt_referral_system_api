"""модуль инициализации fastapi-приложения.

содержит настройку приложения, подключение маршрутов и управление жизненным циклом приложения.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.main import api_router
from app.core.config import settings
from app.core.redis import get_redis


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = await get_redis()

    yield

    await redis.close()


app: FastAPI = FastAPI(
    title=settings.PROJECT_NAME,
    summary=settings.PROJECT_SUMMARY,
    description=settings.PROJECT_DESCRIPTION,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "showExtensions": True,
    },
)

app.include_router(api_router)
