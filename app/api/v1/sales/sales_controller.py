from fastapi import HTTPException, status

from repos.v1.sales import (
    CreateSale,
    UpdateSale,
    SaleInDb,
    SalesRepository,
    SalesDataSource,
)

from core.sale_register.sale_register import SaleRegister


class SalesController:
    def __init__(self, sales_repo: SalesRepository) -> None:
        self.sales_repo = sales_repo
        self.sale_register = SaleRegister()

    async def create_sale(self, body: CreateSale) -> SaleInDb:
        sale, _ = await self.sale_register.regis_sale(body)
        return sale

    async def get_all_sales(self) -> list[SaleInDb]:
        sales = await self.sales_repo.get_all_sales()
        return sales

    async def get_sale_by_id(self, sale_id: str) -> SaleInDb:
        sale = await self.sales_repo.get_sale_by_id(sale_id)
        if sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found",
            )
        return sale

    async def update_sale_by_id(self, sale_id: str, body: UpdateSale) -> SaleInDb:
        updated_sale = await self.sales_repo.update_sale_by_id(sale_id, body)
        if updated_sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found",
            )
        return updated_sale

    async def delete_sale_by_id(self, sale_id: str) -> SaleInDb:
        deleted_sale = await self.sales_repo.delete_sale_by_id(sale_id)
        if deleted_sale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found",
            )
        return deleted_sale


sales_controller = SalesController(
    sales_repo=SalesRepository(
        sales_ds=SalesDataSource(),
    ),
)
