from pydantic import BaseModel
from repos.v1.invoices import InvoiceInDb
from repos.v1.clients import ClientInDb


class InvoiceResponse(BaseModel):
    invoice: InvoiceInDb
    clientAccount: ClientInDb


class InvoiceAnonResponse(BaseModel):
    invoice: InvoiceInDb


class InvoicesWithTotalResponse(BaseModel):
    count: int
    data: list[InvoiceInDb]
    total: int
    totalCost: int
