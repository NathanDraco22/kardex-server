from typing import Any
from services.mongo_collections.v1 import ClientTransactionsCollection


class ClientTransactionsDataSource:
    async def create_client_transaction(
        self, client_transaction: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ClientTransactionsCollection()
        await collection.create_client_transaction(client_transaction)
        return client_transaction

    async def get_all_client_transactions(self, **kwargs) -> list[dict[str, Any]]:
        collection = ClientTransactionsCollection()
        return await collection.fetch_all_client_transactions(**kwargs)

    async def get_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.fetch_client_transaction_by_id(client_transaction_id)

    async def update_client_transaction_by_id(
        self, client_transaction_id: str, client_transaction: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.update_client_transaction_by_id(
            client_transaction_id, client_transaction
        )

    async def delete_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = ClientTransactionsCollection()
        return await collection.delete_client_transaction_by_id(client_transaction_id)
