from typing import Any
from datetime import datetime
from services.mongo_collections.v1 import EntryDocsCollection


class EntryHistoriesDataSource:
    async def get_entry_history(
        self,
        branch_id: str,
        supplier_id: str | None,
        offset: int,
        limit: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        collection = EntryDocsCollection()
        return await collection.fetch_entry_docs_with_supplier(
            branch_id,
            supplier_id,
            offset,
            limit,
            start_date,
            end_date,
        )
