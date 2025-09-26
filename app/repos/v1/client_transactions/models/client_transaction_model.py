from typing import Literal
from pydantic import BaseModel


TransactionType = Literal["credit", "debit"]


class BaseClientTransaction(BaseModel):
    documentId: str
    clientId: str
    amount: int
    type: TransactionType
    resultBalance: int


class ClientTransactionInDb(BaseClientTransaction):
    id: str
    createdAt: int
