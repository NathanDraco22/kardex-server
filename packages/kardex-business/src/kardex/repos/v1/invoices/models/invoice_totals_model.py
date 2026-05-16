from pydantic import BaseModel


class InvoiceTotals(BaseModel):
    paymentType: str | None = None
    total: int
    totalCost: int
    count: int = 0
