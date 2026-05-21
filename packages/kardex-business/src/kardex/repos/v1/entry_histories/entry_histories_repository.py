from .data.entry_histories_datasource import EntryHistoriesDataSource
from .models.entry_history_model import EntryHistoryInDb
from .params.get_entry_history_params import GetEntryHistoryParams

class EntryHistoriesRepository:
    _instance: "EntryHistoriesRepository | None" = None

    def __init__(self, entry_histories_ds: EntryHistoriesDataSource):
        self.entry_histories_ds = entry_histories_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EntryHistoriesRepository(
                entry_histories_ds=EntryHistoriesDataSource()
            )
        return cls._instance

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

    async def get_entry_history_by_id_with_supplier(
        self, entry_doc_id: str
    ) -> EntryHistoryInDb | None:
        res = await self.entry_histories_ds.get_entry_history_by_id_with_supplier(
            entry_doc_id
        )
        if res is None:
            return None

        return EntryHistoryInDb.model_validate(res)

    async def get_entry_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> EntryHistoryInDb | None:
        res = (
            await self.entry_histories_ds.get_entry_history_by_doc_number_and_branch_id(
                doc_number, branch_id
            )
        )

        if res is None:
            return None

        return EntryHistoryInDb.model_validate(res)
