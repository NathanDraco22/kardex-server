from .data.adjust_entries_datasource import AdjustEntriesDataSource
from .models.adjust_entry_model import (
    UpdateAdjustEntry,
    AdjustEntryInDb,
)


class AdjustEntriesRepository:
    def __init__(self, adjust_entries_ds: AdjustEntriesDataSource):
        self.adjust_entries_ds = adjust_entries_ds

    async def get_all_adjust_entries(self, **kwargs) -> list[AdjustEntryInDb]:
        results = await self.adjust_entries_ds.get_all_adjust_entries(**kwargs)
        models = [AdjustEntryInDb.model_validate(result) for result in results]
        return models

    async def get_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> AdjustEntryInDb | None:
        result = await self.adjust_entries_ds.get_adjust_entry_by_id(adjust_entry_id)

        if result is None:
            return None

        return AdjustEntryInDb.model_validate(result)

    async def get_adjust_entry_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> AdjustEntryInDb | None:
        result = await self.adjust_entries_ds.get_adjust_entry_by_doc_number(
            doc_number, branch_id
        )

        if result is None:
            return None

        return AdjustEntryInDb.model_validate(result)

    async def update_adjust_entry_by_id(
        self, adjust_entry_id: str, adjust_entry: UpdateAdjustEntry
    ) -> AdjustEntryInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> AdjustEntryInDb | None:
        result = await self.adjust_entries_ds.delete_adjust_entry_by_id(adjust_entry_id)

        if result is None:
            return None

        return AdjustEntryInDb.model_validate(result)
