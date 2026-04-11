from pydantic import BaseModel


class ProductStockDemand(BaseModel):
    productId: str
    productName: str
    totalOrdered: int
    totalBonification: int
    currentStock: int
    shortage: int
