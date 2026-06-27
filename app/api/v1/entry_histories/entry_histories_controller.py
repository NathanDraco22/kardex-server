from fastapi import HTTPException
from kardex.repos.v1.entry_histories import (
    EntryHistoryInDb,
    EntryHistoriesRepository,
    EntryHistoriesDataSource,
)

from responses.v1 import ListResponse

from kardex.repos.v1.common.filter_params import EntryHistoryFilterParams


class EntryHistoriesController:
    def __init__(self, entry_histories_repo: EntryHistoriesRepository) -> None:
        self.entry_histories_repo = entry_histories_repo

    async def get_entry_history(
        self, query_params: EntryHistoryFilterParams
    ) -> ListResponse[EntryHistoryInDb]:
        entry_histories = await self.entry_histories_repo.get_entry_history(
            params=query_params
        )
        return ListResponse(count=len(entry_histories), data=entry_histories)

    async def get_history_by_id_with_supplier(
        self, entry_doc_id: str
    ) -> EntryHistoryInDb:
        entry_history = (
            await self.entry_histories_repo.get_entry_history_by_id_with_supplier(
                entry_doc_id
            )
        )
        if not entry_history:
            raise HTTPException(status_code=404, detail="Entry history not found")
        return entry_history

    async def get_entry_docs_by_product_id(
        self, product_id: str
    ) -> ListResponse[EntryHistoryInDb]:
        results = await self.entry_histories_repo.get_entry_docs_by_product_id(product_id)
        return ListResponse(count=len(results), data=results)

    async def get_entry_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> EntryHistoryInDb:
        entry_history = await self.entry_histories_repo.get_entry_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
        if not entry_history:
            raise HTTPException(status_code=404, detail="Entry history not found")
        return entry_history


entry_histories_controller = EntryHistoriesController(
    entry_histories_repo=EntryHistoriesRepository(
        entry_histories_ds=EntryHistoriesDataSource(),
    ),
)
