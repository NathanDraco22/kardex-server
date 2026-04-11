from pydantic import BaseModel


class CreateInitialBalance(BaseModel):
    branchId: str
    clientId: str
    initialBalance: int
    productName: str = ""


class InitBalanceITem(BaseModel):
    initialBalance: int
    productName: str = "SALDO INICIAL"


class CreateMultipleInitialBalance(BaseModel):
    branchId: str
    clientId: str
    initialBalances: list[InitBalanceITem]
