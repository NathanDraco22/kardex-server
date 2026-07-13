from pydantic import BaseModel


class InventoryProduct(BaseModel):
    id: str
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    isActive: bool = True
    image: str = ""


class BaseInventory(BaseModel):
    branchId: str
    product: InventoryProduct
    currentStock: int
    averageCost: int
    lastCost: int


class InventoryInDb(BaseInventory):
    createdAt: int
    updatedAt: int | None = None
