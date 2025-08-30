from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ClientTransactionsCollection


class ClientTransactionsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_client_transaction(self, client_transaction: dict[str, Any]) -> dict[str, Any]:
        collection = ClientTransactionsCollection()
        await collection.create_client_transaction(client_transaction)
        return client_transaction

    async def get_all_client_transactions(self) -> list[dict[str, Any]]:
        collection = ClientTransactionsCollection()
        return await collection.fetch_all_client_transactions()

    async def get_client_transaction_by_id(self, client_transaction_id: str) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.fetch_client_transaction_by_id(client_transaction_id)

    async def update_client_transaction_by_id(
        self, client_transaction_id: str, client_transaction: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.update_client_transaction_by_id(client_transaction_id, client_transaction)

    async def delete_client_transaction_by_id(self, client_transaction_id: str) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.delete_client_transaction_by_id(client_transaction_id)
