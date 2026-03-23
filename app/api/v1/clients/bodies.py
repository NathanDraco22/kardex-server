from pydantic import BaseModel


class CreateInitialBalance(BaseModel):
    branchId: str
    clientId: str
    initialBalance: int
    productName: str = ""
