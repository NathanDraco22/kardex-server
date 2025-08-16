from .data.products_datasource import ProductsDataSource
from .models.product_model import (
    CreateProduct,
    UpdateProduct,
    ProductInDb,
    ProductInDbWithAccounts,
)

from tools import UuidTool, TimeTools, generate_prefixes


class ProductsRepository:
    def __init__(self, products_ds: ProductsDataSource):
        self.products_ds = products_ds

    async def create_product(self, create_product: CreateProduct) -> ProductInDb:
        new_product = ProductInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_utc(),
            **create_product.model_dump(),
        )

        new_product_data = new_product.model_dump()
        new_product_data["searchPrefixes"] = generate_prefixes(new_product_data["name"])

        result = await self.products_ds.create_product(new_product_data)

        return ProductInDb.model_validate(result)

    async def get_all_products(self) -> list[ProductInDb]:
        results = await self.products_ds.get_all_products()
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_all_products_with_accounts(
        self, branch_id: str, page: int, limit: int
    ) -> list[ProductInDbWithAccounts]:
        results = await self.products_ds.get_all_products_with_accounts(
            branch_id,
            page,
            limit,
        )
        models = [ProductInDbWithAccounts.model_validate(result) for result in results]
        return models

    async def get_paginated_products(
        self, offset: int, limit: int
    ) -> list[ProductInDb]:
        results = await self.products_ds.get_paginated_products(offset, limit)
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.get_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def search_product_by_text(self, text_query: str) -> list[ProductInDb]:
        results = await self.products_ds.search_product_by_text(text_query)
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_product_by_ids(self, product_ids: list[str]) -> list[ProductInDb]:
        result = await self.products_ds.get_product_by_ids(product_ids)

        return [ProductInDb.model_validate(product) for product in result]

    async def update_product_by_id(
        self, product_id: str, product: UpdateProduct
    ) -> ProductInDb | None:
        updated_data = product.model_dump(exclude_unset=True)

        updated_data["updatedAt"] = TimeTools.get_now_utc()

        updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

        result = await self.products_ds.update_product_by_id(product_id, updated_data)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def delete_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.delete_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)
