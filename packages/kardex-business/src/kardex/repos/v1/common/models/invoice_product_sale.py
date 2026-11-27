from pydantic import BaseModel


class ProductSalesTotal(BaseModel):
    productId: str
    productName: str
    totalQuantity: int
    totalBonQuantity: int
    total: int


class ProductSalesSummary(BaseModel):
    productId: str
    totalQuantity: int
    totalBonQuantity: int
    total: int
    invoiceCount: int
