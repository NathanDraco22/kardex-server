from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ExpirationLogsCollection


class ExpirationLogsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_expiration_log(
        self, expiration_log: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ExpirationLogsCollection()
        await collection.create_expiration_log(expiration_log)
        return expiration_log

    async def get_all_expiration_logs(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExpirationLogsCollection()
        return await collection.fetch_all_expiration_logs(**kwargs)

    async def get_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection()
        return await collection.fetch_expiration_log_by_id(expiration_log_id)

    async def update_expiration_log_by_id(
        self, expiration_log_id: str, expiration_log: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection()
        return await collection.update_expiration_log_by_id(
            expiration_log_id, expiration_log
        )

    async def delete_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> dict[str, Any] | None:
        collection = ExpirationLogsCollection()
        return await collection.delete_expiration_log_by_id(expiration_log_id)
