from pydantic import BaseModel


class InvoiceQueryParams(BaseModel):
    clientId: str | None = None
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    offset: int = 0
    limit: int = 50
