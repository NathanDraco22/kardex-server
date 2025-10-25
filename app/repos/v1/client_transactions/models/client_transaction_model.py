from typing import Literal
from pydantic import BaseModel


TransactionType = Literal["credit", "debit"]
TransactionSubType = Literal[
    "invoice",
    "discount",
    "devolution",
    "receipt",
]


class BaseClientTransaction(BaseModel):
    documentId: str
    clientId: str
    amount: int
    type: TransactionType
    subtype: TransactionSubType
    resultBalance: int


class ClientTransactionInDb(BaseClientTransaction):
    id: str
    createdAt: int
