from typing import Literal
from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo

ExpensesStatus = Literal["draft", "open", "paid", "partiallyPaid", "cancelled"]


class BaseExpense(BaseModel):
    branchId: str
    docNumber: str = ""
    amount: int
    category: str
    description: str | None = None
    date: int
    dateId: str
    amountPaid: int = 0
    status: ExpensesStatus
    isActive: bool = True
    expirationDate: int | None = None
    createdBy: UserInfo
    paidAt: int | None = None



class CreateExpense(BaseExpense):
    pass


class UpdateExpense(BaseModel):
    amount: int | None = None
    amountPaid: int | None = None
    category: str | None = None
    description: str | None = None
    date: int | None = None
    dateId: str | None = None
    isActive: bool | None = None



class ExpenseInDb(BaseExpense):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None


class AddToAmountRequest(BaseModel):
    expenseId: str
    amountPaid: int

