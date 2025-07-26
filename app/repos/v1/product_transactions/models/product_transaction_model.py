from datetime import datetime
from typing import Literal
from pydantic import BaseModel

TransactionType = Literal["ENTRY", "EXIT"]


class BaseProductTransaction(BaseModel):
    documentId: str
    type: TransactionType
    productId: str
    branchId: str
    quantity: int
    averageCost: int


class ProductTransactionInDb(BaseProductTransaction):
    id: str
    createdAt: datetime
