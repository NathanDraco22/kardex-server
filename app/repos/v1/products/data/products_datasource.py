from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ProductsCollection


class ProductsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_product(self, product: dict[str, Any]) -> dict[str, Any]:
        collection = ProductsCollection()
        await collection.create_product(product)
        return product

    async def get_all_products(self) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.fetch_all_products()

    async def get_paginated_products(
        self, offset: int, limit: int
    ) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.fetch_paginated_products(offset, limit)

    async def get_all_products_with_accounts(
        self,
        branch_id: str,
        page: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.fetch_all_products_with_accounts(branch_id, page, limit)

    async def get_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = ProductsCollection()
        return await collection.fetch_product_by_id(product_id)

    async def search_product_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.search_product_by_text(text_query)

    async def search_product_in_branch(
        self,
        branch_id: str,
        text_query: str,
    ) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.searchProductInBranch(branch_id, text_query)

    async def get_all_product_in_branch(self, **kwargs) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.get_all_product_in_branch(**kwargs)

    async def get_product_in_branch_by_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = ProductsCollection()
        return await collection.get_product_in_branch_by_id(product_id, branch_id)

    async def get_product_by_ids(self, product_ids: list[str]) -> list[dict[str, Any]]:
        collection = ProductsCollection()
        return await collection.fetch_product_by_ids(product_ids)

    async def update_product_by_id(
        self, product_id: str, product: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ProductsCollection()
        return await collection.update_product_by_id(product_id, product)

    async def delete_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = ProductsCollection()
        return await collection.delete_product_by_id(product_id)
