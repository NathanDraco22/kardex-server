from .data.entry_docs_datasource import EntryDocsDataSource
from .models.entry_doc_model import EntryDocInDb, EntryHistoryInDb
from kardex.repos.v1.common.filter_params import EntryDocFilterParams

class EntryDocsRepository:
    _instance: "EntryDocsRepository | None" = None

    def __init__(self, entry_docs_ds: EntryDocsDataSource):
        self.entry_docs_ds = entry_docs_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EntryDocsRepository(
                entry_docs_ds=EntryDocsDataSource()
            )
        return cls._instance

    async def get_all_entry_docs(self) -> list[EntryDocInDb]:
        results = await self.entry_docs_ds.get_all_entry_docs()
        models = [EntryDocInDb.model_validate(result) for result in results]
        return models

    async def get_paginated_entry_docs(
        self, params: EntryDocFilterParams
    ) -> list[EntryDocInDb]:
        results = await self.entry_docs_ds.get_paginated_entry_docs(
            params.offset, params.limit, params.branch_id
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

    async def get_entry_history(
        self, params: EntryDocFilterParams
    ) -> list[EntryHistoryInDb]:
        mapped_kwargs = {
            "branch_id": params.branch_id,
            "supplier_id": params.supplierId,
            "offset": params.offset,
            "limit": params.limit,
            "start_date": params.startDate,
            "end_date": params.endDate,
        }
        results = await self.entry_docs_ds.get_entry_history(**mapped_kwargs)
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
