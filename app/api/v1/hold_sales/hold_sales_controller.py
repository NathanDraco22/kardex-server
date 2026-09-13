from typing import Any
from fastapi import HTTPException, status

from kardex.repos.v1.common.filter_params import HoldSaleFilterParams
from kardex.repos.v1.hold_sales import (
    CreateHoldSale,
    UpdateHoldSale,
    HoldSaleInDb,
    HoldSalesRepository,
)
from responses.v1 import ListResponse


class HoldSalesController:
    def __init__(self, hold_sales_repo: HoldSalesRepository) -> None:
        self.hold_sales_repo = hold_sales_repo

    async def create_hold_sale(self, body: CreateHoldSale) -> HoldSaleInDb:
        return await self.hold_sales_repo.create_hold_sale(body)

    async def get_all_hold_sales(
        self, params: HoldSaleFilterParams
    ) -> ListResponse[HoldSaleInDb]:
        hold_sales = await self.hold_sales_repo.get_all_hold_sales(params)
        return ListResponse(count=len(hold_sales), data=hold_sales)

    async def get_hold_sale_by_id(self, hold_sale_id: str) -> HoldSaleInDb:
        hold_sale = await self.hold_sales_repo.get_hold_sale_by_id(hold_sale_id)
        if hold_sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HoldSale not found",
            )
        return hold_sale

    async def update_hold_sale_by_id(
        self, hold_sale_id: str, body: UpdateHoldSale
    ) -> HoldSaleInDb:
        updated_hold_sale = await self.hold_sales_repo.update_hold_sale_by_id(
            hold_sale_id, body
        )
        if updated_hold_sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HoldSale not found",
            )
        return updated_hold_sale

    async def delete_hold_sale_by_id(self, hold_sale_id: str) -> HoldSaleInDb:
        deleted_hold_sale = await self.hold_sales_repo.delete_hold_sale_by_id(
            hold_sale_id
        )
        if deleted_hold_sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HoldSale not found",
            )
        return deleted_hold_sale

    async def delete_all_hold_sales_by_branch(self, branch_id: str) -> dict[str, Any]:
        deleted_count = await self.hold_sales_repo.delete_all_hold_sales_by_branch(
            branch_id
        )
        return {"deletedCount": deleted_count, "branchId": branch_id}


hold_sales_controller = HoldSalesController(
    hold_sales_repo=HoldSalesRepository.get_instance(),
)

