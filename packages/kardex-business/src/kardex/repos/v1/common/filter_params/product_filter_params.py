from typing import Literal
from .base_filter_params import BaseFilterParams
from kardex.repos.v1.common.models.sale_item import ProductType

PaymentMethod = Literal["cash", "transfer", "card", "check", "other"]


class ProductFilterParams(BaseFilterParams):
    branchId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    paymentMethod: PaymentMethod | None = None
    nePaymentMethod: PaymentMethod | None = None
    productType: ProductType | None = None
    onlyInventory: bool | None = None
