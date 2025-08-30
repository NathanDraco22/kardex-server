from pydantic import BaseModel
from repos.v1.invoices import InvoiceInDb
from repos.v1.client_accounts import ClientAccountInDb


class InvoiceResponse(BaseModel):
    invoice: InvoiceInDb
    clientAccount: ClientAccountInDb
