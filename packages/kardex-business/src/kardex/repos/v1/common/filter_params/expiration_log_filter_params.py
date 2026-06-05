from pydantic import BaseModel

class ExpirationLogFilterParams(BaseModel):
    branchId: str | None = None
