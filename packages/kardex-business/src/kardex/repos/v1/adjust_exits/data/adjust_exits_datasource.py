from typing import Any
from kardex.services.mongo_collections.v1 import AdjustExitsCollection


class AdjustExitsDataSource:
    async def create_adjust_exit(self, adjust_exit: dict[str, Any]) -> dict[str, Any]:
        collection = AdjustExitsCollection.get_instance()
        await collection.create_adjust_exit(adjust_exit)
        return adjust_exit

    async def get_all_adjust_exits(self, **kwargs) -> list[dict[str, Any]]:
        collection = AdjustExitsCollection.get_instance()
        return await collection.fetch_all_adjust_exits(**kwargs)

    async def get_adjust_exit_by_id(self, adjust_exit_id: str) -> dict[str, Any] | None:
        collection = AdjustExitsCollection.get_instance()
        return await collection.fetch_adjust_exit_by_id(adjust_exit_id)

    async def get_adjust_exit_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustExitsCollection.get_instance()
        return await collection.fetch_adjust_exit_by_doc_number(doc_number, branch_id)

    async def update_adjust_exit_by_id(
        self, adjust_exit_id: str, adjust_exit: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = AdjustExitsCollection.get_instance()
        return await collection.update_adjust_exit_by_id(adjust_exit_id, adjust_exit)

    async def delete_adjust_exit_by_id(
        self, adjust_exit_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustExitsCollection.get_instance()
        return await collection.delete_adjust_exit_by_id(adjust_exit_id)
