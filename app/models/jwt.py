from sqlmodel import Field, SQLModel


class JWT(SQLModel):
    token: str


class JWTPayload(SQLModel):
    token_type: str
    token_subject: str
    token_expiration: str
    token_subject_user_agent: str


class JWTsPair(SQLModel):
    tokens_type: str = "bearer jwt"
    access_token: JWT
    refresh_token: JWT
