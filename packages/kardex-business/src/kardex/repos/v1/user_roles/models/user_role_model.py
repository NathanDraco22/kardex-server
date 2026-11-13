from pydantic import BaseModel


class BaseUserRole(BaseModel):
    name: str
    access: list[str]


class CreateUserRole(BaseUserRole):
    pass


class UpdateUserRole(BaseModel):
    name: str | None = None
    access: list[str] | None = None


class UserRoleInDb(BaseUserRole):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDefault: bool = False


class SubModuleItem(BaseModel):
    key: str
    name: str
    description: str


class ModuleItem(BaseModel):
    key: str
    name: str
    description: str
    submodules: list[SubModuleItem] = []


class ModulesCatalogResponse(BaseModel):
    allAccessKey: str
    modules: list[ModuleItem]
