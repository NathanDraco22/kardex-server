from .data.transfers_datasource import TransfersDataSource
from .models.transfer_model import TransferInDb


class TransfersRepository:
    def __init__(self, transfers_ds: TransfersDataSource):
        self.transfers_ds = transfers_ds

    async def get_all_transfers(self, **kwargs) -> list[TransferInDb]:
        results = await self.transfers_ds.get_all_transfers(**kwargs)
        models = [TransferInDb.model_validate(result) for result in results]
        return models

    async def get_transfer_by_id(self, transfer_id: str) -> TransferInDb | None:
        result = await self.transfers_ds.get_transfer_by_id(transfer_id)

        if result is None:
            return None

        return TransferInDb.model_validate(result)

    async def get_transfer_by_doc_number(self, doc_number: str) -> TransferInDb | None:
        result = await self.transfers_ds.get_transfer_by_doc_number(doc_number)

        if result is None:
            return None

        return TransferInDb.model_validate(result)
