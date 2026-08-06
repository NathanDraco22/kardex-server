from typing import Any
from kardex.services.mongo_collections.v1.api_keys_collection import ApiKeysCollection


class ApiKeysDataSource:
    def __init__(self) -> None:
        self.collection = ApiKeysCollection()

    async def create_api_key(self, api_key_dict: dict[str, Any]) -> None:
        await self.collection.create_api_key(api_key_dict)

    async def get_all_api_keys(self) -> list[dict[str, Any]]:
        return await self.collection.fetch_all_api_keys()

    async def get_api_key_by_id(self, key_id: str) -> dict[str, Any] | None:
        return await self.collection.fetch_api_key_by_id(key_id)

    async def get_api_key_by_value(self, key_value: str) -> dict[str, Any] | None:
        return await self.collection.fetch_api_key_by_value(key_value)

    async def toggle_api_key_status(self, key_id: str, is_active: bool) -> dict[str, Any] | None:
        return await self.collection.toggle_api_key_status(key_id, is_active)

    async def update_last_used_at(self, key_id: str, timestamp: int) -> None:
        await self.collection.update_last_used_at(key_id, timestamp)

    async def delete_api_key_by_id(self, key_id: str) -> dict[str, Any] | None:
        return await self.collection.delete_api_key_by_id(key_id)
