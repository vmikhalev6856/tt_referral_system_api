"""модуль управления пользователями и реферальной системой.

содержит функции для создания пользователей, аутентификации и получения списка рефералов.

copyright (c) 2025 vladislav mikhalev, all rights reserved.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.core.utils import check_email_validity
from app.models import ReferralCode
from app.models.user import LoginUser, RegisterUser, User, UserReferrals, UserView


async def create_user(
    user: RegisterUser,
    database_session: AsyncSession,
) -> UserView:
    """создает нового пользователя в базе данных, основываясь на переданных данных для регистрации.

    Args:
        user (RegisterUser): данные для регистрации пользователя (email, password, referral_code (опционально))
        database_session (AsyncSession): асинхронная сессия базы данных

    Returns:
        UserView: объект, содержащий информацию о созданном пользователе

    Raises:
        HTTPException: если пользователь с таким email уже существует или email не прошел проверку (403 forbidden).
            а так же если указан неверный реферальный код (400 bad request)

    """
    existing_user = await database_session.scalar(select(User).where(User.email == user.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="такой пользователь уже есть, email занят",
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
                detail="реферальный код отозван или введен неверно",
            )

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        referrer_id=referrer_data.id if referrer_data else None,
    )

    database_session.add(new_user)
    await database_session.commit()
    await database_session.refresh(new_user)

    return UserView.model_validate(
        new_user,
        update={"referral_code": None},
    )


async def authenticate_user(
    user: LoginUser,
    database_session: AsyncSession,
) -> UserView:
    """аутентифицирует пользователя по логину и паролю.

    Args:
        user (LoginUser): данные пользователя для входа (email и пароль)
        database_session (AsyncSession): асинхронная сессия базы данных

    Raises:
        HTTPException: если аутентификация не удалась из-за неверных учетных данных

    Returns:
        UserView: объект пользователя без лишних данных

    """
    existing_user = await database_session.scalar(
        select(User).where(User.email == user.email).options(joinedload(User.referral_code)),
    )

    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="неверный email или пароль")

    return UserView.model_validate(existing_user)


async def get_user_refferals(
    user: UserView,
    database_session: AsyncSession,
) -> AsyncSession:
    """возвращает информацию о пользователе и его рефералах.

    Args:
        user (UserView): объект userview текущего пользователя
        database_session (AsyncSession): асинхронная сессия базы данных

    Returns:
        AsyncSession: объект с количеством и списком рефералов

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
