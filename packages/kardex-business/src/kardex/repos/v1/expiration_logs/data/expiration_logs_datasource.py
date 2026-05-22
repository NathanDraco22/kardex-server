from typing import Any
from kardex.services.mongo_collections.v1 import ExpirationLogsCollection


class ExpirationLogsDataSource:
    async def create_expiration_log(
        self, expiration_log: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ExpirationLogsCollection.get_instance()
        await collection.create_expiration_log(expiration_log)
        return expiration_log

    async def create_many_expiration_logs(self, expiration_logs: list[dict[str, Any]]):
        collection = ExpirationLogsCollection.get_instance()
        await collection.create_many_expiration_logs(expiration_logs)

    async def get_all_expiration_logs(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExpirationLogsCollection.get_instance()
        return await collection.fetch_all_expiration_logs(**kwargs)

    async def get_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection.get_instance()
        return await collection.fetch_expiration_log_by_id(expiration_log_id)

    async def update_expiration_log_by_id(
        self, expiration_log_id: str, expiration_log: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection.get_instance()
        return await collection.update_expiration_log_by_id(
            expiration_log_id, expiration_log
        )

    async def delete_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection.get_instance()
        return await collection.delete_expiration_log_by_id(expiration_log_id)

    async def has_near_expiration_date(self, target_date: int, branch_id: str) -> bool:
        collection = ExpirationLogsCollection.get_instance()
        return await collection.has_near_expiration_date(target_date, branch_id)
