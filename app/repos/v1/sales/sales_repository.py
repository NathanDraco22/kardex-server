from .data.sales_datasource import SalesDataSource
from .models.sale_model import CreateSale, UpdateSale, SaleInDb


class SalesRepository:
    def __init__(self, sales_ds: SalesDataSource):
        self.sales_ds = sales_ds

    async def create_sale(self, create_sale: CreateSale) -> SaleInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_sales(self) -> list[SaleInDb]:
        results = await self.sales_ds.get_all_sales()
        models = [SaleInDb.model_validate(result) for result in results]
        return models

    async def get_sale_by_id(self, sale_id: str) -> SaleInDb | None :
        result = await self.sales_ds.get_sale_by_id(sale_id)
        
        if result is None:
            return None
        
        return SaleInDb.model_validate(result)

    async def update_sale_by_id(self, sale_id: str, sale: UpdateSale) -> SaleInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_sale_by_id(self, sale_id: str) -> SaleInDb | None:
        result = await self.sales_ds.delete_sale_by_id(sale_id)
        
        if result is None:
            return None
        
        return SaleInDb.model_validate(result)
