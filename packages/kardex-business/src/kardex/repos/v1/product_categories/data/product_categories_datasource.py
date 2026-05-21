from typing import Any
from kardex.services.mongo_collections.v1 import ProductCategoriesCollection


class ProductCategoriesDataSource:
    async def create_product_category(self, product_category: dict[str, Any]) -> dict[str, Any]:
        collection = ProductCategoriesCollection.get_instance()
        await collection.create_product_category(product_category)
        return product_category

    async def get_all_product_categories(self) -> list[dict[str, Any]]:
        collection = ProductCategoriesCollection.get_instance()
        return await collection.fetch_all_product_categories()

    async def get_product_category_by_id(self, product_category_id: str) -> dict[str, Any] | None:
        collection = ProductCategoriesCollection.get_instance()
        return await collection.fetch_product_category_by_id(product_category_id)

    async def update_product_category_by_id(
        self, product_category_id: str, product_category: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ProductCategoriesCollection.get_instance()
        return await collection.update_product_category_by_id(product_category_id, product_category)

    async def delete_product_category_by_id(self, product_category_id: str) -> dict[str, Any] | None:
        collection = ProductCategoriesCollection.get_instance()
        return await collection.delete_product_category_by_id(product_category_id)
