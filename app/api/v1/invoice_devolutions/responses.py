from pydantic import BaseModel
from repos.v1.invoices import InvoiceInDb
from repos.v1.devolutions import DevolutionInDb


class InvoiceDevolutionsResponse(BaseModel):
    invoice: InvoiceInDb
    devolutions: list[DevolutionInDb]
