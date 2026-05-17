from typing import Any

from kardex.services.mongo_collections.v1 import ExitDocsCollection


class ExitHistoriesDataSource:
    async def get_exit_history(
        self,
        branch_id: str,
        client_id: str | None,
        offset: int,
        limit: int,
        start_date: int | None = None,
        end_date: int | None = None,
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

    async def get_exit_doc_history_by_id_with_client(
        self, exit_doc_id: str
    ) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_id_with_client(exit_doc_id)

    async def get_exit_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_doc_number_and_branch(
            doc_number, branch_id
        )
