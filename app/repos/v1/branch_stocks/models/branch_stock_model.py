from pydantic import BaseModel


class BaseBranchStock(BaseModel):
    product_id: str
    branch_id: str
    current_stock: int
    average_cost: float
    last_cost: float
    pass


class UpdateBranchStock(BaseBranchStock):
    pass


class BranchStockInDb(BaseBranchStock):
    updated_at: int | None = None
