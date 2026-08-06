from pydantic import BaseModel


class BaseApiKey(BaseModel):
    name: str
    serviceType: str = "power_bi"  # "power_bi", "ecommerce", "custom"
    scopes: list[str] = ["bi:read"]
    branchId: str | None = None


class CreateApiKey(BaseApiKey):
    pass


class ApiKeyInDb(BaseApiKey):
    id: str
    key: str  # npt_live_...
    maskedKey: str  # npt_live_k9X2...4hJ1
    isActive: bool = True
    createdAt: int
    lastUsedAt: int | None = None
    createdBy: str | None = None


class CreatedApiKeyResponse(ApiKeyInDb):
    rawKey: str
