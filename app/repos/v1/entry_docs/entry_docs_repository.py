from .data.entry_docs_datasource import EntryDocsDataSource
from .models.entry_doc_model import EntryDocInDb


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
