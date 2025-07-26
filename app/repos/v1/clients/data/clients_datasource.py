from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ClientsCollection


class ClientsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_client(self, client: dict[str, Any]) -> dict[str, Any]:
        collection = ClientsCollection()
        await collection.create_client(client)
        return client

    async def get_all_clients(self) -> list[dict[str, Any]]:
        collection = ClientsCollection()
        return await collection.fetch_all_clients()

    async def get_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = ClientsCollection()
        return await collection.fetch_client_by_id(client_id)

    async def update_client_by_id(
        self, client_id: str, client: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientsCollection()
        return await collection.update_client_by_id(client_id, client)
