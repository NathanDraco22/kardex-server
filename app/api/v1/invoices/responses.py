from pydantic import BaseModel
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.clients import ClientInDb


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
