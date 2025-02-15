"""модуль конфигурации базы данных.

модуль предоставляет конфигурацию движка базы данных
и управление сессиями для асинхронных операций sqlalchemy

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from app.core.config import settings

async_database_engine: AsyncEngine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))


database_async_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(async_database_engine, class_=AsyncSession)


async def get_async_database_session() -> AsyncGenerator[AsyncSession]:
    """создает и возвращает асинхронную сессию базы данных.

    это зависимость, которая может быть использована в эндпоинтах fastapi для получения
    сессии базы данных. сессия автоматически закрывается, когда генератор завершает работу

    Yields:
        async_database_session: асинхронная сессия sqlalchemy,
        которая может быть использована для операций с базой данных

    """
    async with database_async_sessionmaker() as async_database_session:
        yield async_database_session
