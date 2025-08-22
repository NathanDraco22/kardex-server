from datetime import datetime, time

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
        start_date: datetime | None = None
        end_date: datetime | None = None

        if query_params.start_date and query_params.end_date:
            start_date = datetime.combine(query_params.start_date, time.min)
            end_date = datetime.combine(query_params.end_date, time.max)

            if start_date > end_date:
                start_date = None
                end_date = None

        entry_domain_params = GetEntryHistoryParams(
            branch_id=query_params.branch_id,
            supplier_id=query_params.supplier_id,
            offset=query_params.offset,
            limit=query_params.limit,
            start_date=start_date,
            end_date=end_date,
        )

        entry_histories = await self.entry_histories_repo.get_entry_history(
            params=entry_domain_params
        )
        return ListResponse(count=len(entry_histories), data=entry_histories)


entry_histories_controller = EntryHistoriesController(
    entry_histories_repo=EntryHistoriesRepository(
        entry_histories_ds=EntryHistoriesDataSource(),
    ),
)
