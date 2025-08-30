from fastapi import APIRouter

from repos.v1.sales import CreateSale, UpdateSale, SaleInDb

from .sales_controller import sales_controller


sales_router = APIRouter(tags=["salesV1"])


@sales_router.post("")
async def create_sale(body: CreateSale) -> SaleInDb:
    return await sales_controller.create_sale(body)


@sales_router.get("")
async def get_all_sales() -> list[SaleInDb]:
    return await sales_controller.get_all_sales()


@sales_router.get("/{sale_id}")
async def get_sale_by_id(sale_id: str) -> SaleInDb:
    return await sales_controller.get_sale_by_id(sale_id)


@sales_router.patch("/{sale_id}")
async def update_sale_by_id(sale_id: str, body: UpdateSale) -> SaleInDb: 
    return await sales_controller.update_sale_by_id(sale_id, body)


@sales_router.delete("/{sale_id}")
async def delete_sale_by_id(sale_id: str) -> SaleInDb:
    return await sales_controller.delete_sale_by_id(sale_id)
