from typing import Literal
from pydantic import BaseModel

TransactionType = Literal[
    "entry",
    "exit",
]
TransactionSubType = Literal[
    "entry",
    "exit",
    "invoice",
    "return",
]


class BaseProductTransaction(BaseModel):
    documentId: str
    type: TransactionType
    subtype: TransactionSubType
    productId: str
    branchId: str
    quantity: int
    averageCost: int
    resultStock: int


class ProductTransactionInDb(BaseProductTransaction):
    id: str
    createdAt: int
