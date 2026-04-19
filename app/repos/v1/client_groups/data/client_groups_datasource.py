from typing import Any
from services.mongo_collections.v1 import ClientGroupsCollection


class ClientGroupsDataSource:
    async def create_client_group(self, client_group: dict[str, Any]) -> dict[str, Any]:
        collection = ClientGroupsCollection()
        await collection.create_client_group(client_group)
        return client_group

    async def get_all_client_groups(self) -> list[dict[str, Any]]:
        collection = ClientGroupsCollection()
        return await collection.fetch_all_client_groups()

    async def get_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = ClientGroupsCollection()
        return await collection.fetch_client_group_by_id(client_group_id)

    async def update_client_group_by_id(
        self, client_group_id: str, client_group: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ClientGroupsCollection()
        return await collection.update_client_group_by_id(client_group_id, client_group)

    async def delete_client_group_by_id(self, client_group_id: str) -> dict[str, Any] | None:
        collection = ClientGroupsCollection()
        return await collection.delete_client_group_by_id(client_group_id)
