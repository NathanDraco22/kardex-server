from pydantic import BaseModel


class BaseExpense(BaseModel):
    branchId: str
    amount: int
    category: str
    description: str | None = None
    date: int
    dateId: str
    createdBy: str
    docNumber: str = ""
    isActive: bool = True


class CreateExpense(BaseExpense):
    pass


class UpdateExpense(BaseModel):
    amount: int | None = None
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
