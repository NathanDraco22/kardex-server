from pydantic import BaseModel


class ReceiptTotal(BaseModel):
    total: int
