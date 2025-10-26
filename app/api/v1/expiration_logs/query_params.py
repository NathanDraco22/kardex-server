from pydantic import BaseModel


class ExpirationLogQueryParams(BaseModel):
    branchId: str | None = None
