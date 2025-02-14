"""модуль маршрутов API.

модуль включает маршруты для работы с пользователями и реферальными кодами.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import APIRouter

from app.api.routes import referral_code, user

api_router = APIRouter()


api_router.include_router(
    user.user_router,
    prefix="/user",
    tags=["user"],
)


api_router.include_router(
    referral_code.referrral_code_router,
    prefix="/referral_code",
    tags=["referral code"],
)
