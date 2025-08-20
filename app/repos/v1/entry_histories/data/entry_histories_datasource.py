from typing import Any
from services.mongo_collections.v1 import EntryDocsCollection


class EntryHistoriesDataSource:
    async def get_entry_history(
        self, branch_id: str, supplier_id: str, offset: int, limit: int
    ) -> list[dict[str, Any]]:
        collection = EntryDocsCollection()
        return await collection.fetch_entry_docs_with_supplier(
            branch_id,
            supplier_id,
            offset,
            limit,
        )
