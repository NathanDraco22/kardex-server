from pydantic import BaseModel
from repos.v1.common.models import Coordinates


class BaseBranch(BaseModel):
    name: str
    idCard: str = ""
    address: str = ""
    email: str = ""
    phone: str = ""
    image: str = ""
    description: str = ""
    isCommerce: bool = True
    coordinates: Coordinates | None = None


class CreateBranch(BaseBranch):
    pass


class UpdateBranch(BaseModel):
    name: str | None = None
    idCard: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    description: str | None = None
    image: str | None = None


class BranchInDb(BaseBranch):
    id: str
    createdAt: int
    updatedAt: int | None = None
