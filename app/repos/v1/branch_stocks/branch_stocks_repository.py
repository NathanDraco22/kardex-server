from .data.branch_stocks_datasource import BranchStocksDataSource
from .models.branch_stock_model import UpdateBranchStock, BranchStockInDb

from tools import TimeTools


class BranchStocksRepository:
    def __init__(self, branch_stocks_ds: BranchStocksDataSource):
        self.branch_stocks_ds = branch_stocks_ds

    async def create_branch_stock(self, branch_stock: BranchStockInDb) -> None:
        await self.branch_stocks_ds.create_branch_stock(branch_stock.model_dump())

    async def get_branch_stock_by_id(
        self, branch_stock_id: str
    ) -> BranchStockInDb | None:
        res = await self.branch_stocks_ds.get_branch_stock_by_id(branch_stock_id)

        if res is None:
            return None

        return BranchStockInDb.model_validate(res)

    async def get_branch_stock_by_branch_and_product_id(
        self, product_id: str, branch_id: str
    ) -> BranchStockInDb | None:
        res = await self.branch_stocks_ds.get_branch_stock_by_branch_and_product_id(
            product_id, branch_id
        )

        if res is None:
            return None

        return BranchStockInDb.model_validate(res)

    async def update_branch_stock_by_id(
        self, branch_stock_id: str, update_branch_stock: UpdateBranchStock
    ) -> BranchStockInDb:
        update_branch_stock_data = update_branch_stock.model_dump()

        update_branch_stock_data["updated_at"] = TimeTools.get_now_in_milliseconds()

        res = await self.branch_stocks_ds.update_branch_stock_by_id(
            branch_stock_id,
            update_branch_stock_data,
        )

        return BranchStockInDb.model_validate(res)

    async def update_branch_stock_by_branch_and_product_id(
        self, product_id: str, branch_id: str, update_branch_stock: UpdateBranchStock
    ) -> BranchStockInDb:
        update_branch_stock_data = update_branch_stock.model_dump()

        update_branch_stock_data["updated_at"] = TimeTools.get_now_in_milliseconds()

        res = await self.branch_stocks_ds.update_branch_stock_by_branch_and_product_id(
            product_id,
            branch_id,
            update_branch_stock_data,
        )

        return BranchStockInDb.model_validate(res)
