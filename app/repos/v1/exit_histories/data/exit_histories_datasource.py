from typing import Any
from datetime import datetime
from services.mongo_collections.v1 import ExitDocsCollection


class ExitHistoriesDataSource:
    async def get_exit_history(
        self,
        branch_id: str,
        client_id: str | None,
        offset: int,
        limit: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_docs_with_client(
            branch_id,
            client_id,
            offset,
            limit,
            start_date,
            end_date,
        )
