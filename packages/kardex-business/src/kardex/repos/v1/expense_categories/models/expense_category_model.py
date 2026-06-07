from pydantic import BaseModel


class BaseExpenseCategory(BaseModel):
    name: str


class CreateExpenseCategory(BaseExpenseCategory):
    pass


class UpdateExpenseCategory(BaseModel):
    name: str | None = None


class ExpenseCategoryInDb(BaseExpenseCategory):
    id: str
    createdAt: int
    updatedAt: int | None = None
