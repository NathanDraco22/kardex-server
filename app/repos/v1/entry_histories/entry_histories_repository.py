from .data.entry_histories_datasource import EntryHistoriesDataSource
from .models.entry_history_model import EntryHistoryInDb
from .params.get_entry_history_params import GetEntryHistoryParams


class EntryHistoriesRepository:
    def __init__(self, entry_histories_ds: EntryHistoriesDataSource):
        self.entry_histories_ds = entry_histories_ds

    async def get_entry_history(
        self, params: GetEntryHistoryParams
    ) -> list[EntryHistoryInDb]:
        entry_histories_data = await self.entry_histories_ds.get_entry_history(
            **params.to_dict()
        )

        entry_histories = [
            EntryHistoryInDb.model_validate(entry_history)
            for entry_history in entry_histories_data
        ]
        return entry_histories
