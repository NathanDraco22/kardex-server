from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ProductTransactionsCollection


class ProductTransactionsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_product_transaction(
        self, product_transaction: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ProductTransactionsCollection()
        await collection.create_product_transaction(product_transaction)
        return product_transaction

    async def get_all_product_transactions(self, **kwargs) -> list[dict[str, Any]]:
        collection = ProductTransactionsCollection()
        return await collection.fetch_all_product_transactions(**kwargs)

    async def get_product_transaction_by_id(
        self, product_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = ProductTransactionsCollection()
        return await collection.fetch_product_transaction_by_id(product_transaction_id)
