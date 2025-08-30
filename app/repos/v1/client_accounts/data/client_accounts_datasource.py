from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ClientAccountsCollection


class ClientAccountsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_client_account(self, client_account: dict[str, Any]) -> dict[str, Any]:
        collection = ClientAccountsCollection()
        await collection.create_client_account(client_account)
        return client_account

    async def get_all_client_accounts(self) -> list[dict[str, Any]]:
        collection = ClientAccountsCollection()
        return await collection.fetch_all_client_accounts()

    async def get_client_account_by_id(self, client_account_id: str) -> dict[str, Any] | None:
        collection = ClientAccountsCollection()
        return await collection.fetch_client_account_by_id(client_account_id)

    async def update_client_account_by_id(
        self, client_account_id: str, client_account: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientAccountsCollection()
        return await collection.update_client_account_by_id(client_account_id, client_account)

    async def delete_client_account_by_id(self, client_account_id: str) -> dict[str, Any] | None:
        collection = ClientAccountsCollection()
        return await collection.delete_client_account_by_id(client_account_id)
