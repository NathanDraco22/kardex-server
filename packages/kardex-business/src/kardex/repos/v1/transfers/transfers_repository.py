from .data.transfers_datasource import TransfersDataSource
from .models.transfer_model import TransferInDb
from kardex.repos.v1.common.filter_params import TransferFilterParams


class TransfersRepository:
    _instance: "TransfersRepository | None" = None

    def __init__(self, transfers_ds: TransfersDataSource):
        self.transfers_ds = transfers_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TransfersRepository(transfers_ds=TransfersDataSource())
        return cls._instance

    async def get_all_transfers(
        self, params: TransferFilterParams
    ) -> list[TransferInDb]:
        results = await self.transfers_ds.get_all_transfers(
            **params.model_dump(exclude_none=True)
        )
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
