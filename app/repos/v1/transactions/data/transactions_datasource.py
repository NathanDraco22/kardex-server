from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import TransactionsCollection


class TransactionsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        collection = TransactionsCollection()
        await collection.create_transaction(transaction)
        return transaction

    async def get_all_transactions(self) -> list[dict[str, Any]]:
        collection = TransactionsCollection()
        return await collection.fetch_all_transactions()

    async def get_transaction_by_id(self, transaction_id: str) -> dict[str, Any] | None:
        collection = TransactionsCollection()
        return await collection.fetch_transaction_by_id(transaction_id)
