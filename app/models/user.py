from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

from app.models import ReferralCode


class User(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    email: EmailStr = Field(unique=True, max_length=64)
    hashed_password: str = Field(max_length=60)
    referral_code: ReferralCode | None = Relationship(back_populates="user")
    referrer_id: UUID | None

    __table_args__ = (
        Index("user_id_hash_index", "id", postgresql_using="hash"),
        Index("user_email_hash_index", "email", postgresql_using="hash"),
    )


class UserView(SQLModel):
    id: UUID
    email: EmailStr
    referral_code: ReferralCode | None
    referrer_id: UUID | None


class LoginUser(SQLModel):
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=64)


class RefreshLoginUser(SQLModel):
    refresh_token: str = Field(regex=r"^bearer jwt\s[\w-]+\.[\w-]+\.[\w-]+$")


class RegisterUser(LoginUser):
    referral_code: str | None = None


class UserReferrals(UserView):
    referrals_count: int
    referrals_list: list[UserView | None]


class UserRegistrationsAvailableCount(SQLModel):
    registrations_available_count: int


class UserEmail(SQLModel):
    email: EmailStr


class UserReferralCode(UserEmail):
    referral_code: str | None
