from .data.entry_histories_datasource import EntryHistoriesDataSource
from .models.entry_history_model import EntryHistoryInDb


class EntryHistoriesRepository:
    def __init__(self, entry_histories_ds: EntryHistoriesDataSource):
        self.entry_histories_ds = entry_histories_ds

    async def get_entry_history(
        self, branch_id: str, supplier_id: str, offset: int, limit: int
    ) -> list[EntryHistoryInDb]:
        entry_histories_data = await self.entry_histories_ds.get_entry_history(
            branch_id,
            supplier_id,
            offset,
            limit,
        )

        entry_histories = [
            EntryHistoryInDb.model_validate(entry_history)
            for entry_history in entry_histories_data
        ]
        return entry_histories
