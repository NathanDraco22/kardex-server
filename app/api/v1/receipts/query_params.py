from pydantic import BaseModel
from kardex.repos.v1.receipts.models.receipt_model import PaymentMethod


class ReceiptQueryParams(BaseModel):
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    paymentMethod: PaymentMethod | None = None
    nePaymentMethod: PaymentMethod | None = None
    endDate: int | None = None
    offset: int = 0
    limit: int = 50
