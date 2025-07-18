import uuid

from tools import TimeTools

from .data.products_datasource import ProductsDataSource
from .models.product_model import CreateProduct, UpdateProduct, ProductInDb


class ProductsRepository:
    def __init__(self, products_ds: ProductsDataSource):
        self.products_ds = products_ds

    async def create_product(self, create_product: CreateProduct) -> ProductInDb:
        product_in_db = ProductInDb(
            id=str(uuid.uuid4()),
            created_at=TimeTools.get_now_in_milliseconds(),
            **create_product.model_dump(),
        )

        await self.products_ds.create_product(product_in_db.model_dump())
        return product_in_db

    async def get_all_products(self) -> list[ProductInDb]:
        results = await self.products_ds.get_all_products()
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.get_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def get_product_by_sku(self, sku: str) -> ProductInDb | None:
        result = await self.products_ds.get_product_by_sku(sku)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def update_product_by_id(
        self, product_id: str, product: UpdateProduct
    ) -> ProductInDb | None:
        data_to_update = product.model_dump(exclude_unset=True)

        data_to_update["updated_at"] = TimeTools.get_now_in_milliseconds()

        result = await self.products_ds.update_product_by_id(product_id, data_to_update)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def delete_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.delete_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)
