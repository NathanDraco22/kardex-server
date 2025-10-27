from pydantic import BaseModel


class TransactionQueryParams(BaseModel):
    branchId: str | None = None
    productId: str | None = None
    endDate: int | None = None
    type: str | None = None
    subtype: str | None = None
    offset: int = 0
    limit: int = 50
