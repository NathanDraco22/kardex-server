from pydantic import BaseModel
from kardex.repos.v1.invoices import InvoiceTotals


class AdminChartsResponses(BaseModel):
    last7DaysTotals: list[InvoiceTotals]
