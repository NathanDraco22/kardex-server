from pydantic import BaseModel, Field


class RoleCapabilities(BaseModel):
    allowInvoicing: bool = True
    allowCreditInvoicing: bool = True
    showClientCreditDetails: bool = True


class BaseUserRole(BaseModel):
    name: str
    access: list[str]
    capabilities: RoleCapabilities = Field(default_factory=RoleCapabilities)


class CreateUserRole(BaseUserRole):
    pass


class UpdateUserRole(BaseModel):
    name: str | None = None
    access: list[str] | None = None
    capabilities: RoleCapabilities | None = None


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
