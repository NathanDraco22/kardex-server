from pydantic import BaseModel


class InvoiceTotals(BaseModel):
    total: int
