"""модуль настроек приложения.

модуль определяет настройки приложения, используя pydantic для управления переменными окружения.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from datetime import timedelta

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """класс настроек приложения.

    этот класс определяет все параметры конфигурации, требующиеся для приложения,
    которые извлекаются из переменных окружения.
    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str
    PROJECT_SUMMARY: str
    PROJECT_DESCRIPTION: str
    DEVELOPMENT_PROJECT_NAME: str

    EMAIL_HUNTER_API_URL: str
    EMAIL_HUNTER_API_KEY: str

    SECRET_KEY: str
    SIGNING_ALGORITHM: str
    ACCESS_TOKEN_TIMEDELTA: timedelta = timedelta(minutes=15)
    REFRESH_TOKEN_TIMEDELTA: timedelta = timedelta(days=3)

    TIMEZONE: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:  # noqa: N802
        """формирует uri для подключения к базе данных sqlalchemy.

        это свойство динамически генерирует uri для подключения к базе данных,
        используя конфигурационные данные для подключения к postgres.

        возвращает:
            PostgresDsn: отформатированный uri базы данных, подходящий для sqlalchemy.
        """
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


settings: Settings = Settings()
