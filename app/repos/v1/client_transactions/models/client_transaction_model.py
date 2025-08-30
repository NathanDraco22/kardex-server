from datetime import datetime
from typing import Literal
from pydantic import BaseModel


TransactionType = Literal["CREDIT", "DEBIT"]


class BaseClientTransaction(BaseModel):
    documentId: str
    clientId: str
    amount: int
    type: TransactionType


class ClientTransactionInDb(BaseClientTransaction):
    id: str
    createdAt: datetime
