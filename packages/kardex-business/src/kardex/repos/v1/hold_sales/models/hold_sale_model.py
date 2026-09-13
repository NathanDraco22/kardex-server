from pydantic import BaseModel, Field
from kardex.repos.v1.common.models import PaymentType, UserInfo
from kardex.repos.v1.clients.models.client_model import ClientInDb
from kardex.repos.v1.products.models.product_model import ProductInDbInBranch
from kardex.repos.v1.product_sale_profiles.models.product_sale_profile_model import Discount


class HoldSaleItem(BaseModel):
    product: ProductInDbInBranch
    newPrice: int
    selectedPriceLevel: int = 1
    quantity: int
    selectedUnitIndex: int = 0
    conversionFactor: int = 1
    selectedUnitName: str = ""
    selectedDiscount: Discount | None = None


class BaseHoldSale(BaseModel):
    branchId: str
    client: ClientInDb | None = None
    selectedPriceLevel: int = 1
    isWholesale: bool = False
    description: str = ""
    selectedPaymentType: PaymentType = "cash"
    items: list[HoldSaleItem] = Field(default_factory=list)
    totalQuantity: int = 0
    totalAmount: int = 0
    createdBy: UserInfo | None = None


class CreateHoldSale(BaseHoldSale):
    pass


class UpdateHoldSale(BaseModel):
    description: str | None = None
    client: ClientInDb | None = None
    selectedPriceLevel: int | None = None
    isWholesale: bool | None = None
    selectedPaymentType: PaymentType | None = None
    items: list[HoldSaleItem] | None = None
    totalQuantity: int | None = None
    totalAmount: int | None = None


class HoldSaleInDb(BaseHoldSale):
    id: str
    createdAt: int
    updatedAt: int | None = None
