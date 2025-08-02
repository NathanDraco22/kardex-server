from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ProductPricesCollection


class ProductPricesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_product_price(self, product_price: dict[str, Any]) -> dict[str, Any]:
        collection = ProductPricesCollection()
        await collection.create_product_price(product_price)
        return product_price

    async def get_all_product_prices(self) -> list[dict[str, Any]]:
        collection = ProductPricesCollection()
        return await collection.fetch_all_product_prices()

    async def get_product_price_by_id(self, product_price_id: str) -> dict[str, Any] | None:
        collection = ProductPricesCollection()
        return await collection.fetch_product_price_by_id(product_price_id)

    async def update_product_price_by_id(
        self, product_price_id: str, product_price: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ProductPricesCollection()
        return await collection.update_product_price_by_id(product_price_id, product_price)

    async def delete_product_price_by_id(self, product_price_id: str) -> dict[str, Any] | None:
        collection = ProductPricesCollection()
        return await collection.delete_product_price_by_id(product_price_id)
