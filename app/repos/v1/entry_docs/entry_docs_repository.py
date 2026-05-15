from .data.entry_docs_datasource import EntryDocsDataSource
from .models.entry_doc_model import EntryDocInDb, EntryHistoryInDb


class EntryDocsRepository:
    def __init__(self, entry_docs_ds: EntryDocsDataSource):
        self.entry_docs_ds = entry_docs_ds

    async def get_all_entry_docs(self) -> list[EntryDocInDb]:
        results = await self.entry_docs_ds.get_all_entry_docs()
        models = [EntryDocInDb.model_validate(result) for result in results]
        return models

    async def get_paginated_entry_docs(
        self, offset: int, limit: int, branch_id: str
    ) -> list[EntryDocInDb]:
        results = await self.entry_docs_ds.get_paginated_entry_docs(
            offset, limit, branch_id
        )
        models = [EntryDocInDb.model_validate(result) for result in results]
        return models

    async def get_entry_doc_by_id(self, entry_doc_id: str) -> EntryDocInDb | None:
        result = await self.entry_docs_ds.get_entry_doc_by_id(entry_doc_id)

        if result is None:
            return None

        return EntryDocInDb.model_validate(result)

    async def get_entry_doc_by_doc_number(self, doc_number: str) -> EntryDocInDb | None:
        result = await self.entry_docs_ds.get_entry_doc_by_doc_number(doc_number)

        if result is None:
            return None

        return EntryDocInDb.model_validate(result)

    async def get_entry_doc_by_doc_number_and_supplier(
        self, supplier_id: str, doc_number: str
    ) -> EntryDocInDb | None:
        result = await self.entry_docs_ds.get_entry_doc_by_doc_number_and_supplier(
            supplier_id, doc_number
        )

        if result is None:
            return None

        return EntryDocInDb.model_validate(result)

    async def get_entry_history(self, **kwargs) -> list[EntryHistoryInDb]:
        results = await self.entry_docs_ds.get_entry_history(**kwargs)
        return [EntryHistoryInDb.model_validate(result) for result in results]

    async def get_entry_history_by_id_with_supplier(
        self, entry_doc_id: str
    ) -> EntryHistoryInDb | None:
        result = await self.entry_docs_ds.get_entry_history_by_id_with_supplier(
            entry_doc_id
        )
        if result is None:
            return None
        return EntryHistoryInDb.model_validate(result)

    async def get_entry_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> EntryHistoryInDb | None:
        result = await self.entry_docs_ds.get_entry_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
        if result is None:
            return None
        return EntryHistoryInDb.model_validate(result)
