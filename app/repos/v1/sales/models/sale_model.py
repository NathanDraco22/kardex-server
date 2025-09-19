from pydantic import BaseModel
from repos.v1.common.models import SaleItem


class BaseSale(BaseModel):
    branchId: str
    saleItems: list[SaleItem]
    description: str = ""
    totalCost: int
    total: int


class CreateSale(BaseSale):
    pass


class UpdateSale(BaseModel):
    pass


class SaleInDb(BaseSale):
    id: str
    createdAt: int
    updatedAt: int | None = None
