from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ClientsCollection, ClientAccountsCollection


class ClientsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_client(self, client: dict[str, Any]) -> dict[str, Any]:
        collection = ClientsCollection()
        client_accounts_collection = ClientAccountsCollection()
        await collection.create_client(client)

        account_data = {
            "clientId": client["id"],
            "balance": 0,
            "createdAt": client["createdAt"],
        }

        await client_accounts_collection.create_client_account(account_data)
        return client

    async def get_all_clients(self) -> list[dict[str, Any]]:
        collection = ClientsCollection()
        return await collection.fetch_all_clients()

    async def get_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = ClientsCollection()
        return await collection.fetch_client_by_id(client_id)

    async def search_client_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = ClientsCollection()
        return await collection.search_client_by_text(text_query)

    async def update_client_by_id(
        self, client_id: str, client: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientsCollection()
        return await collection.update_client_by_id(client_id, client)
