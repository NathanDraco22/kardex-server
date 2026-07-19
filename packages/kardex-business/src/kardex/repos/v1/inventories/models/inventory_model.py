from pydantic import BaseModel
from kardex.repos.v1.products.models.product_model import ExtraUnit


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
    extraUnits: list[ExtraUnit] = []
    defaultUnitIndex: int = 0

    @property
    def default_unit_name(self) -> str:
        """Nombre de la unidad por defecto para display."""
        if self.defaultUnitIndex == 0 or not self.extraUnits:
            return self.unitName
        idx = self.defaultUnitIndex - 1
        if 0 <= idx < len(self.extraUnits):
            return self.extraUnits[idx].name
        return self.unitName

    @property
    def default_unit_factor(self) -> int:
        """Factor de conversión de la unidad por defecto."""
        if self.defaultUnitIndex == 0 or not self.extraUnits:
            return 1
        idx = self.defaultUnitIndex - 1
        if 0 <= idx < len(self.extraUnits):
            return self.extraUnits[idx].conversionFactor
        return 1


class BaseInventory(BaseModel):
    branchId: str
    product: InventoryProduct
    currentStock: int
    averageCost: int
    lastCost: int


class InventoryInDb(BaseInventory):
    createdAt: int
    updatedAt: int | None = None
