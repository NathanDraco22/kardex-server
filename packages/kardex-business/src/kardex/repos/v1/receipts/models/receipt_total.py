from pydantic import BaseModel
from .receipt_model import PaymentMethod


class ReceiptTotal(BaseModel):
    paymentMethod: PaymentMethod | None = None
    total: int
    count: int = 0
