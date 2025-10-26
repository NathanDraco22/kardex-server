from fastapi import HTTPException

from repos.v1.entry_histories import (
    EntryHistoryInDb,
    EntryHistoriesRepository,
    EntryHistoriesDataSource,
    GetEntryHistoryParams,
)

from responses.v1 import ListResponse

from .query_params import EntryHistoryQueryParams


class EntryHistoriesController:
    def __init__(self, entry_histories_repo: EntryHistoriesRepository) -> None:
        self.entry_histories_repo = entry_histories_repo

    async def get_entry_history(
        self, query_params: EntryHistoryQueryParams
    ) -> ListResponse[EntryHistoryInDb]:
        entry_domain_params = GetEntryHistoryParams(
            branch_id=query_params.branchId,
            supplier_id=query_params.supplierId,
            offset=query_params.offset,
            limit=query_params.limit,
            start_date=query_params.startDate,
            end_date=query_params.endDate,
        )

        entry_histories = await self.entry_histories_repo.get_entry_history(
            params=entry_domain_params
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
