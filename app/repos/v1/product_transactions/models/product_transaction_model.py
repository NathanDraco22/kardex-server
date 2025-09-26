from typing import Literal
from pydantic import BaseModel

TransactionType = Literal["entry", "exit", "sale", "invoice"]


class BaseProductTransaction(BaseModel):
    documentId: str
    type: TransactionType
    productId: str
    branchId: str
    quantity: int
    averageCost: int
    resultStock: int


class ProductTransactionInDb(BaseProductTransaction):
    id: str
    createdAt: int
