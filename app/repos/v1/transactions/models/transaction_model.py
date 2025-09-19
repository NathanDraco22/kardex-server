from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field


TransactionType = Literal["ENTRY", "EXIT"]


class BaseTransaction(BaseModel):
    accountId: str
    branchId: str
    quantity: int


class CreateExitTransaction(BaseTransaction):
    type: Literal["EXIT"] = "EXIT"
    quantity: int = Field(..., lt=0)


class CreateEntryTransaction(BaseTransaction):
    type: Literal["ENTRY"] = "ENTRY"
    quantity: int = Field(..., gt=0)


class TransactionInDb(BaseTransaction):
    id: str
    type: TransactionType
    createdAt: int


class BatchEntryItem(BaseModel):
    accountId: str
    quantity: int = Field(..., gt=0)


class BatchEntryTransaction(BaseModel):
    branchId: str
    type: Literal["ENTRY"] = "ENTRY"
    items: list[BatchEntryItem]


class BatchExitItem(BaseModel):
    accountId: str
    quantity: int = Field(..., lt=0)


class BatchExitTransaction(BaseModel):
    branchId: str
    type: Literal["EXIT"] = "EXIT"
    items: list[BatchExitItem]


CreateTransaction = Annotated[
    Union[CreateExitTransaction, CreateEntryTransaction],
    Field(discriminator="type"),
]
