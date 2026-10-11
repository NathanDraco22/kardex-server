from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_sale_profiles import ProductSaleProfileInDb

from pydantic import BaseModel


class ExtraUnit(BaseModel):
    name: str = ""
    conversionFactor: int = 1


class BaseProduct(BaseModel):
    name: str
    description: str | None = None
    code: str = ""
    altCode: str = ""
    image: str = ""
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str]
    hasIva: bool = False
    isActive: bool = True
    extraUnits: list[ExtraUnit] = []
    defaultUnitIndex: int = 0  # 0 = unidad base, 1 = extraUnits[0], 2 = extraUnits[1]
    wholesaleUnitIndex: int = 0  # 0 = no definida, fallback a defaultUnitIndex

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
    isActive: bool | None = None
    extraUnits: list[ExtraUnit] | None = None
    defaultUnitIndex: int | None = None
    wholesaleUnitIndex: int | None = None



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

