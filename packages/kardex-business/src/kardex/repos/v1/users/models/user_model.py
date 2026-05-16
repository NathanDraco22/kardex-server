from pydantic import BaseModel


class UserRole(BaseModel):
    name: str
    access: list[str]


class BaseUser(BaseModel):
    username: str
    password: str
    isActive: bool = True
    isInternal: bool = False
    role: str
    branches: list[str] = []


class CreateUser(BaseUser):
    pass


class UpdateUser(BaseModel):
    username: str | None = None
    isActive: bool | None = None
    role: str | None = None
    branches: list[str] | None = None


class UserInDb(BaseUser):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None


class UserInDbWithRole(UserInDb):
    userRole: UserRole
