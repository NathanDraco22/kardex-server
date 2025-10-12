from pydantic import BaseModel


class DecodedCoreSetting(BaseModel):
    name: str
    nickname: str
    ownerName: str
    isMultiBranch: bool
    isActive: bool
    price: int


class BaseCoreSetting(BaseModel):
    token: str


class CreateCoreSetting(BaseCoreSetting):
    pass


class UpdateCoreSetting(BaseModel):
    token: str | None = None


class CoreSettingInDb(BaseCoreSetting):
    id: str
    createdAt: int
    updatedAt: int | None = None
