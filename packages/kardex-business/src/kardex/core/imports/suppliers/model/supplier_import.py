from pydantic import BaseModel


class SupplierImport(BaseModel):
    name: str
    cardId: str | None = None
    email: str | None = None
    phone: str | None = None
