from typing import Any

from kardex.services.mongo_collections.v1 import EntryDocsCollection


class EntryHistoriesDataSource:
    async def get_entry_history(
        self,
        branch_id: str,
        supplier_id: str | None,
        offset: int,
        limit: int,
        start_date: int | None = None,
        end_date: int | None = None,
    ) -> list[dict[str, Any]]:
        collection = EntryDocsCollection.get_instance()
        return await collection.fetch_entry_docs_with_supplier(
            branch_id,
            supplier_id,
            offset,
            limit,
            start_date,
            end_date,
        )

    async def get_entry_history_by_id_with_supplier(
        self, entry_doc_id: str
    ) -> dict[str, Any] | None:
        collection = EntryDocsCollection.get_instance()
        return await collection.fetch_entry_doc_by_id_with_supplier(entry_doc_id)

    async def get_entry_docs_by_product_id(
        self, product_id: str
    ) -> list[dict[str, Any]]:
        collection = EntryDocsCollection.get_instance()
        return await collection.fetch_entry_docs_by_product_id(product_id)

    async def get_entry_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = EntryDocsCollection.get_instance()
        return await collection.fetch_entry_doc_by_doc_number_and_branch(
            branch_id, doc_number
        )
