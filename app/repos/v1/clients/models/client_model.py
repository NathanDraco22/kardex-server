from pydantic import BaseModel
from repos.v1.common.models import Coordinates


class PersonalReference(BaseModel):
    name: str
    phone: str
    address: str
    location: str
    email: str | None = None


class BaseClient(BaseModel):
    name: str
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
    balance: int = 0
    creditLimit: int = 0
    lastCreditStart: int | None = None
    lastReceiptDate: int | None = None
    isCreditActive: bool = False
    isActive: bool = True
    group: str = ""
    coordinates: Coordinates | None = None
    personalReferences: list[PersonalReference] = []


class CreateClient(BaseClient):
    initialBalance: int = 0
    pass


class UpdateClient(BaseModel):
    name: str | None = None
    cardId: str | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    email: str | None = None
    isActive: bool | None = None
    isCreditActive: bool | None = None
    creditLimit: int | None = None
    group: str | None = None
    coordinates: Coordinates | None = None
    personalReferences: list[PersonalReference] | None = None


class ClientInDb(BaseClient):
    id: str
    isDeleted: bool = False
    isInternal: bool = False
    hasMovements: bool = False
    createdAt: int
    updatedAt: int | None = None
