from typing import Any
from kardex.services.mongo_collections.v1 import ExitDocsCollection


class ExitDocsDataSource:
    async def create_exit_doc(self, exit_doc: dict[str, Any]) -> dict[str, Any]:
        collection = ExitDocsCollection()
        await collection.create_exit_doc(exit_doc)
        return exit_doc

    async def get_all_exit_docs(self) -> list[dict[str, Any]]:
        collection = ExitDocsCollection()
        return await collection.fetch_all_exit_docs()

    async def get_paginated_exit_docs(
        self,
        offset: int,
        limit: int,
        branch_id: str,
    ) -> list[dict[str, Any]]:
        collection = ExitDocsCollection()
        return await collection.fetch_paginated_exit_docs(offset, limit, branch_id)

    async def get_exit_doc_by_id(self, exit_doc_id: str) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_id(exit_doc_id)

    async def get_exit_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_doc_number(doc_number)

    async def get_exit_doc_by_doc_number_and_client(
        self, client_id: str, doc_number: str
    ) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_doc_number_and_client(
            client_id,
            doc_number,
        )

    async def get_exit_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_docs_with_client(**kwargs)

    async def get_exit_history_by_id_with_client(
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
