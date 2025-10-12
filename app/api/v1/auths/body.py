from pydantic import BaseModel


class LoginBody(BaseModel):
    userId: str
    password: str


class ChangePasswordBody(BaseModel):
    userId: str
    oldPassword: str
    newPassword: str


class RefreshTokenBody(BaseModel):
    token: str
