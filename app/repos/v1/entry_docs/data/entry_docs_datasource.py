from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import EntryDocsCollection


class EntryDocsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_entry_doc(self, entry_doc: dict[str, Any]) -> dict[str, Any]:
        collection = EntryDocsCollection()
        await collection.create_entry_doc(entry_doc)
        return entry_doc

    async def get_all_entry_docs(self) -> list[dict[str, Any]]:
        collection = EntryDocsCollection()
        return await collection.fetch_all_entry_docs()

    async def get_paginated_entry_docs(
        self, offset: int, limit: int, branch_id: str
    ) -> list[dict[str, Any]]:
        collection = EntryDocsCollection()
        return await collection.fetch_paginated_entry_docs(offset, limit, branch_id)

    async def get_entry_doc_by_id(self, entry_doc_id: str) -> dict[str, Any] | None:
        collection = EntryDocsCollection()
        return await collection.fetch_entry_doc_by_id(entry_doc_id)

    async def get_entry_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = EntryDocsCollection()
        return await collection.fetch_entry_doc_by_doc_number(doc_number)

    async def get_entry_doc_by_doc_number_and_supplier(
        self, supplier_id: str, doc_number: str
    ) -> dict[str, Any] | None:
        collection = EntryDocsCollection()
        return await collection.fetch_entry_doc_by_doc_number_and_supplier(
            supplier_id,
            doc_number,
        )
