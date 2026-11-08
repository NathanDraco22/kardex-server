from typing import Literal
from pydantic import BaseModel

CreditNoteType = Literal["devolution", "amount"]
CreditNoteStatus = Literal["open", "confirmed", "cancelled", "applied"]


class CreditNoteFilterParams(BaseModel):
    branchId: str | None = None
    clientId: str | None = None
    type: CreditNoteType | None = None
    status: CreditNoteStatus | None = None
