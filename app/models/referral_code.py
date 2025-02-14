from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class ReferralCode(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    code: str = Field(unique=True, max_length=16)
    code_expiration: datetime
    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="referral_code")


class ReferralCodeCreate(SQLModel):
    lifetime_in_hours: int = Field(ge=1)
