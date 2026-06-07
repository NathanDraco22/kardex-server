from typing import Literal
from pydantic import BaseModel

DevolutionStatus = Literal["open", "confirmed", "cancelled", "applied"]

class DevolutionFilterParams(BaseModel):
    branchId: str | None = None
    clientId: str | None = None
    status: DevolutionStatus | None = None
