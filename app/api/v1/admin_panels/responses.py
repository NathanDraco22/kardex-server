from pydantic import BaseModel
from repos.v1.invoices import InvoiceTotals


class AdminChartsResponses(BaseModel):
    last7DaysTotals: list[InvoiceTotals]
