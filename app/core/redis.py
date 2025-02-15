"""модуль для работы с redis.

модуль содержит функции для инициализации, получения и закрытия соединения с redis,
используя параметры подключения из конфигурации приложения.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from redis.asyncio.client import Redis

from app.core.config import settings


async def get_redis() -> Redis:
    """возвращает подключение к redis.

    Returns:
        redis: подключение к redis

    """
    return Redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
    )
