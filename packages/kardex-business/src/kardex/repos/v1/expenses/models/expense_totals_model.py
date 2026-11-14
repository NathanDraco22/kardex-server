from pydantic import BaseModel, Field


class ExpenseTypeTotal(BaseModel):
    type: str | None = None
    total: int
    paid: int
    pending: int
    count: int = 0


class ExpenseTotals(BaseModel):
    total: int
    paid: int
    pending: int
    count: int = 0
    byType: list[ExpenseTypeTotal] = Field(default_factory=list)
