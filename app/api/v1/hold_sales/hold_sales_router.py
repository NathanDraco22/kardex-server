from typing import Any
from fastapi import APIRouter, Depends

from app_middleware import auth_middleware
from kardex.repos.v1.common.filter_params import HoldSaleFilterParams
from kardex.repos.v1.hold_sales import CreateHoldSale, UpdateHoldSale, HoldSaleInDb
from responses.v1 import ListResponse

from .hold_sales_controller import hold_sales_controller

hold_sales_router = APIRouter(
    tags=["hold_salesV1"],
    dependencies=[Depends(auth_middleware)],
)


@hold_sales_router.post("")
async def create_hold_sale(body: CreateHoldSale) -> HoldSaleInDb:
    return await hold_sales_controller.create_hold_sale(body)


@hold_sales_router.get("")
async def get_all_hold_sales(
    params: HoldSaleFilterParams = Depends(),
) -> ListResponse[HoldSaleInDb]:
    return await hold_sales_controller.get_all_hold_sales(params)


@hold_sales_router.delete("/branch/{branch_id}")
async def delete_all_hold_sales_by_branch(branch_id: str) -> dict[str, Any]:
    return await hold_sales_controller.delete_all_hold_sales_by_branch(branch_id)


@hold_sales_router.get("/{hold_sale_id}")
async def get_hold_sale_by_id(hold_sale_id: str) -> HoldSaleInDb:
    return await hold_sales_controller.get_hold_sale_by_id(hold_sale_id)


@hold_sales_router.patch("/{hold_sale_id}")
async def update_hold_sale_by_id(
    hold_sale_id: str, body: UpdateHoldSale
) -> HoldSaleInDb:
    return await hold_sales_controller.update_hold_sale_by_id(hold_sale_id, body)


@hold_sales_router.delete("/{hold_sale_id}")
async def delete_hold_sale_by_id(hold_sale_id: str) -> HoldSaleInDb:
    return await hold_sales_controller.delete_hold_sale_by_id(hold_sale_id)

