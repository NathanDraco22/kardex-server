from kardex.repos.v1.common.models.sale_item import ProductType
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_sale_profiles import ProductSaleProfileInDb

from pydantic import BaseModel, Field


class ExtraUnit(BaseModel):
    name: str = ""
    conversionFactor: int = 1


class BaseProduct(BaseModel):
    name: str
    description: str | None = None
    code: str = ""
    altCode: str = ""
    image: str = ""
    brandName: str = ""
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    hasIva: bool = False
    isActive: bool = True
    productType: ProductType = "item"
    branchId: str | None = None
    extraUnits: list[ExtraUnit] = []
    defaultUnitIndex: int = 0  # 0 = unidad base, 1 = extraUnits[0], 2 = extraUnits[1]
    wholesaleUnitIndex: int = 0  # 0 = no definida, fallback a defaultUnitIndex
    priceUnitFactor: int = Field(default=1, ge=1)
    showBasicUnit: bool = True

    @property
    def tracks_inventory(self) -> bool:
        return self.productType == "item"

    @property
    def is_service(self) -> bool:
        return self.productType == "service"

    @property
    def default_unit_name(self) -> str:
        """Nombre de la unidad por defecto para display."""
        if self.defaultUnitIndex == 0 or not self.extraUnits:
            return self.unitName
        idx = self.defaultUnitIndex - 1
        if 0 <= idx < len(self.extraUnits):
            return self.extraUnits[idx].name
        return self.unitName   # fallback

    @property
    def default_unit_factor(self) -> int:
        """Factor de conversión de la unidad por defecto."""
        if self.defaultUnitIndex == 0 or not self.extraUnits:
            return 1
        idx = self.defaultUnitIndex - 1
        if 0 <= idx < len(self.extraUnits):
            return self.extraUnits[idx].conversionFactor
        return 1              # fallback


class CreateProduct(BaseProduct):
    pass


class UpdateProduct(BaseModel):
    name: str | None = None
    code: str | None = None
    altCode: str | None = None
    description: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    categoryName: str | None = None
    tags: list[str] | None = None
    image: str | None = None
    hasIva: bool | None = None
    isActive: bool | None = None
    productType: ProductType | None = None
    # Solo se honra al convertir un artículo (global) en servicio/no inventariable.
    # Para cualquier otra actualización se ignora: la sucursal es inmutable.
    branchId: str | None = None
    extraUnits: list[ExtraUnit] | None = None
    defaultUnitIndex: int | None = None
    wholesaleUnitIndex: int | None = None
    priceUnitFactor: int | None = Field(default=None, ge=1)
    showBasicUnit: bool | None = None



class ProductInDb(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None


class ProductInDbWithAccounts(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
    accounts: list[ProductAccountInDb]


class ProductInDbInBranch(BaseProduct):
    id: str
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
    account: ProductAccountInDb
    saleProfile: ProductSaleProfileInDb


class GetProductsInBranchRequest(BaseModel):
    productIds: list[str]


class InventoryInfo(BaseModel):
    quantity: int
    cost: int
    price: int


class CreateProductWithData(BaseModel):
    createProduct: CreateProduct
    branchId: str
    inventoryInfo: InventoryInfo

