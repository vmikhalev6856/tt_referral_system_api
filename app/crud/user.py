"""модуль управления пользователями и реферальной системой.

содержит функции для создания пользователей, аутентификации и получения списка рефералов.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.core.utils import check_email_validity
from app.models import ReferralCode
from app.models.user import LoginUser, RegisterUser, User, UserReferrals, UserView


async def create_user(user: RegisterUser, database_session: AsyncSession) -> UserView:
    """создает нового пользователя в базе данных с возможностью указания реферального кода.

    аргументы:
        user: данные для регистрации пользователя (email, пароль, опционально - реферальный код).
        database_session: асинхронная сессия базы данных.

    возвращает:
        userview: объект, содержащий информацию о созданном пользователе.

    выбрасывает:
        httpexception: если пользователь с таким email уже существует (403 forbidden)
        или указан неверный реферальный код (400 bad request).
    """
    existing_user = await database_session.scalar(select(User).where(User.email == user.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user with this email already exists.",
        )

    if not await check_email_validity(user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="почтовый ящик не является валидным, не сможет получить письмо",
        )

    referrer_data = None

    if user.referral_code:
        referrer_data = await database_session.scalar(
            select(User).where(User.referral_code.has(ReferralCode.code == user.referral_code)),
        )
        if not referrer_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid referral code (use null or correct code).",
            )

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        referrer_id=referrer_data.id if referrer_data else None,
    )

    try:
        database_session.add(new_user)
        await database_session.commit()
        await database_session.refresh(new_user)

    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User creation failed due to a database error.",
        ) from error

    return UserView.model_validate(
        new_user,
        update={"referral_code": None},
    )


async def authenticate_user(
    user: LoginUser,
    database_session: AsyncSession,
) -> UserView | None:
    """проверяет учетные данные пользователя и возвращает его данные при успешной аутентификации.

    аргументы:
        user: данные пользователя для входа (email и пароль).
        database_session: асинхронная сессия базы данных.

    возвращает:
        userview | none: объект userview, если аутентификация успешна, иначе none.
    """
    existing_user = await database_session.scalar(select(User).where(User.email == user.email))

    if existing_user and verify_password(user.password, existing_user.hashed_password):
        return UserView.model_validate(existing_user, update={"referral_code": None})

    return None


async def get_user_refferals(
    user: UserView,
    database_session: AsyncSession,
) -> UserReferrals:
    """возвращает список пользователей, зарегистрированных по реферальному коду данного пользователя.

    аргументы:
        user: объект userview текущего пользователя.
        database_session: асинхронная сессия базы данных.

    возвращает:
        userreferrals: объект с количеством и списком рефералов.
    """
    referrals = await database_session.scalars(
        select(User).where(User.referrer_id == user.id).options(joinedload(User.referral_code)),
    )

    referrals_list = referrals.all()

    return UserReferrals(
        id=user.id,
        email=user.email,
        referral_code=user.referral_code,
        referrer_id=user.referrer_id,
        referrals_count=len(referrals_list),
        referrals_list=[UserView.model_validate(userview) for userview in referrals_list],
    )
