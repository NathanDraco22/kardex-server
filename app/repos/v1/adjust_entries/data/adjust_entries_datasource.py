from typing import Any
from services.mongo_collections.v1 import AdjustEntriesCollection


class AdjustEntriesDataSource:
    async def create_adjust_entry(self, adjust_entry: dict[str, Any]) -> dict[str, Any]:
        collection = AdjustEntriesCollection()
        await collection.create_adjust_entry(adjust_entry)
        return adjust_entry

    async def get_all_adjust_entries(self, **kwargs) -> list[dict[str, Any]]:
        collection = AdjustEntriesCollection()
        return await collection.fetch_all_adjust_entries(**kwargs)

    async def get_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustEntriesCollection()
        return await collection.fetch_adjust_entry_by_id(adjust_entry_id)

    async def get_adjust_entry_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustEntriesCollection()
        return await collection.fetch_adjust_entry_by_doc_number(doc_number, branch_id)

    async def update_adjust_entry_by_id(
        self, adjust_entry_id: str, adjust_entry: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = AdjustEntriesCollection()
        return await collection.update_adjust_entry_by_id(adjust_entry_id, adjust_entry)

    async def delete_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> dict[str, Any] | None:
        collection = AdjustEntriesCollection()
        return await collection.delete_adjust_entry_by_id(adjust_entry_id)
