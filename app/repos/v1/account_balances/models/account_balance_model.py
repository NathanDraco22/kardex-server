from datetime import datetime
from pydantic import BaseModel


class BaseAccountBalance(BaseModel):
    accountId: str
    branchId: str
    balance: int


class CreateAccountBalance(BaseAccountBalance):
    pass


class UpdateAccountBalance(BaseModel):
    pass


class AccountBalanceInDb(BaseAccountBalance):
    updatedAt: datetime | None = None
