from typing import Any
from kardex.services.mongo_collections.v1 import ProductTransactionsCollection


class ProductTransactionsDataSource:
    async def create_product_transaction(
        self, product_transaction: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ProductTransactionsCollection.get_instance()
        await collection.create_product_transaction(product_transaction)
        return product_transaction

    async def get_all_product_transactions(self, **kwargs) -> list[dict[str, Any]]:
        collection = ProductTransactionsCollection.get_instance()
        return await collection.fetch_all_product_transactions(**kwargs)

    async def get_product_transaction_by_id(
        self, product_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = ProductTransactionsCollection.get_instance()
        return await collection.fetch_product_transaction_by_id(product_transaction_id)

    async def estimate_product_stats(self, **kwargs) -> None:
        collection = ProductTransactionsCollection.get_instance()
        await collection.estimate_invoice_product_stats(**kwargs)
