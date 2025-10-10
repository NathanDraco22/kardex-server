from pydantic import BaseModel
from repos.v1.orders.models.order_model import OrderInDb
from repos.v1.invoices.models.invoice_model import InvoiceInDb


class ConvertOrderToInvoiceResponse(BaseModel):
    invoice: InvoiceInDb
    order: OrderInDb
