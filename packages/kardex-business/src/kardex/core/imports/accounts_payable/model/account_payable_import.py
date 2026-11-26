from pydantic import BaseModel


class AccountPayableImport(BaseModel):
    supplierId: str | None = None
    supplierName: str
    docNumber: str | None = None
    date: int | None = None
    expirationDate: int | None = None
    amount: int
    amountPaid: int = 0
    description: str | None = None
