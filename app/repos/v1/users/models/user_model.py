from pydantic import BaseModel


class UserRole(BaseModel):
    name: str
    access: list[str]


class BaseUser(BaseModel):
    username: str
    password: str
    isActive: bool = True
    role: UserRole


class CreateUser(BaseUser):
    pass


class UpdateUser(BaseModel):
    accsess: list[str] | None = None


class UserInDb(BaseUser):
    id: str
    created_at: int
    updated_at: int | None = None
