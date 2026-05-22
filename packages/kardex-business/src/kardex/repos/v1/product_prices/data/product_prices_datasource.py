from typing import Any
from kardex.services.mongo_collections.v1 import ProductPricesCollection


class ProductPricesDataSource:
    async def create_product_price(self, product_price: dict[str, Any]) -> dict[str, Any]:
        collection = ProductPricesCollection.get_instance()
        await collection.create_product_price(product_price)
        return product_price

    async def get_all_product_prices(self) -> list[dict[str, Any]]:
        collection = ProductPricesCollection.get_instance()
        return await collection.fetch_all_product_prices()

    async def get_product_price_by_id(self, product_price_id: str) -> dict[str, Any] | None:
        collection = ProductPricesCollection.get_instance()
        return await collection.fetch_product_price_by_id(product_price_id)

    async def update_product_price_by_id(
        self, product_price_id: str, product_price: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ProductPricesCollection.get_instance()
        return await collection.update_product_price_by_id(product_price_id, product_price)

    async def delete_product_price_by_id(self, product_price_id: str) -> dict[str, Any] | None:
        collection = ProductPricesCollection.get_instance()
        return await collection.delete_product_price_by_id(product_price_id)
