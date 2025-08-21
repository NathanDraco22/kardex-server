from repos.v1.entry_histories import (
    EntryHistoryInDb,
    EntryHistoriesRepository,
    EntryHistoriesDataSource,
)

from responses.v1 import ListResponse


class EntryHistoriesController:
    def __init__(self, entry_histories_repo: EntryHistoriesRepository) -> None:
        self.entry_histories_repo = entry_histories_repo

    async def get_entry_history(
        self, branch_id: str, supplier_id: str | None, offset: int, limit: int
    ) -> ListResponse[EntryHistoryInDb]:
        entry_histories = await self.entry_histories_repo.get_entry_history(
            branch_id, supplier_id, offset, limit
        )
        return ListResponse(count=len(entry_histories), data=entry_histories)


entry_histories_controller = EntryHistoriesController(
    entry_histories_repo=EntryHistoriesRepository(
        entry_histories_ds=EntryHistoriesDataSource(),
    ),
)
