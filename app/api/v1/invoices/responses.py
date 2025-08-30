from pydantic import BaseModel
from repos.v1.invoices import InvoiceInDb
from repos.v1.clients import ClientInDb


class InvoiceResponse(BaseModel):
    invoice: InvoiceInDb
    clientAccount: ClientInDb
