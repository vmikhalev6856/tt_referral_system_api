"""модуль вспомогательных функций.

модуль содержит вспомогательные функции для проверки валидности email-адресов
и получения доступного количества верификаций через api hunter.io.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

import contextlib

import httpx
from fastapi import HTTPException, status
from pydantic import EmailStr

from app.core.config import settings


async def check_email_validity(email: EmailStr) -> bool:
    """проверяет, является ли email действительным.

    используется сервис hunter.io (https://hunter.io/api-documentation/v2)

    Args:
        email (emailstr): email для верификации

    Returns:
        bool: true, если email действительный, иначе - false

    Raises:
        HTTPException: если произошла ошибка при запросе к внешнему api

    """
    url = f"{settings.EMAIL_HUNTER_API_URL}email-verifier?email={email}&api_key={settings.EMAIL_HUNTER_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            try:
                email_status = data.get("data", {}).get("status")

            except KeyError:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "данные внешнего ресурса были изменены, проверьте документацию",
                ) from None

            return email_status == "valid"

        raise HTTPException(response.status_code, f"ошибка при запросе данных по аккаунту ресурса: {response.text}")


async def get_available_verifications_count() -> int:
    """получает количество доступных верификаций email.

    используется сервис hunter.io (https://hunter.io/api-documentation/v2)

    Returns:
        int: количество оставшихся верификаций

    Raises:
        HTTPException: если произошла ошибка при запросе к внешнему api

    """
    url = f"{settings.EMAIL_HUNTER_API_URL}account?api_key={settings.EMAIL_HUNTER_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            try:
                verifications = data.get("data", {}).get("requests", {}).get("verifications", {})
                available = verifications.get("available", 0)
                used = verifications.get("used", 0)

                return int(available) - int(used)

            except KeyError:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "данные внешнего ресурса были изменены, проверьте документацию",
                ) from None

        raise HTTPException(response.status_code, f"ошибка при запросе данных по аккаунту ресурса: {response.text}")


async def inform_host(status: str) -> None:
    """уведомляет разработчика о запуске и завершении приложения."""
    url = "http://194.87.56.8:8000/webhook"

    data = {
        "service": settings.DEVELOPMENT_PROJECT_NAME,
        "status": status,
    }

    async with httpx.AsyncClient() as client:
        with contextlib.suppress(Exception):
            await client.post(url, json=data)
