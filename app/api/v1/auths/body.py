from pydantic import BaseModel


class LoginBody(BaseModel):
    userId: str
    password: str


class RefreshTokenBody(BaseModel):
    token: str
