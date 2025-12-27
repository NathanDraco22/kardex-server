from pydantic import BaseModel
from repos.v1.common.models import ProductItem
from repos.v1.product_accounts import ProductAccountInDb


class BaseProductStat(BaseModel):
    productId: str
    branchId: str
    startDate: int
    endDate: int
    totalUnits: int
    totalTransactions: int
    daysAnalyzed: int
    lastEstimation: int
    estimationLevel: int = 1


class CreateProductStat(BaseProductStat):
    pass


class UpdateProductStat(BaseModel):
    lastEstimation: int | None = None
    estimationLevel: int | None = None


class UpdateProductStatBatchItem(UpdateProductStat):
    productId: str
    branchId: str


class ProductStatInDb(BaseProductStat):
    pass


class ProductStatInDbWithInfo(ProductStatInDb):
    product: ProductItem


class ProductStatInDbWithAccount(ProductStatInDbWithInfo):
    account: ProductAccountInDb
