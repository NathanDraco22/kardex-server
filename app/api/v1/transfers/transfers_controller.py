from fastapi import HTTPException, status

from core.transfer_manager.transfer_manager import TransferManager

from responses.v1 import ListResponse

from repos.v1.transfers import (
    CreateTransfer,
    TransferInDb,
    TransfersRepository,
    TransfersDataSource,
    ReceiveTransferIntent,
    CancelTransferIntent,
)

from .query_params import TransferQueryParams


class TransfersController:
    def __init__(self, transfers_repo: TransfersRepository) -> None:
        self.transfers_repo = transfers_repo
        self.transfer_manager = TransferManager()

    async def create_transfer(self, body: CreateTransfer) -> TransferInDb:
        transfer, _ = await self.transfer_manager.regis_outgoing_transfer(body)
        return transfer

    async def get_all_transfers(
        self, query: TransferQueryParams
    ) -> ListResponse[TransferInDb]:
        raw_query = query.model_dump(exclude_none=True)
        transfers = await self.transfers_repo.get_all_transfers(**raw_query)
        return ListResponse(
            count=len(transfers),
            data=transfers,
        )

    async def get_transfer_by_id(self, transfer_id: str) -> TransferInDb:
        transfer = await self.transfers_repo.get_transfer_by_id(transfer_id)
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )
        return transfer

    async def get_transfer_by_doc_number(self, doc_number: str) -> TransferInDb:
        transfer = await self.transfers_repo.get_transfer_by_doc_number(doc_number)
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )
        return transfer

    async def receive_transfer(
        self, transfer_id: str, intent: ReceiveTransferIntent
    ) -> TransferInDb:
        transfer, _ = await self.transfer_manager.regis_incoming_transfer(
            transfer_id, intent
        )
        return transfer

    async def cancel_transfer(
        self, transfer_id: str, intent: CancelTransferIntent
    ) -> TransferInDb:
        transfer, _ = await self.transfer_manager.cancel_transfer(transfer_id, intent)
        return transfer


transfers_controller = TransfersController(
    transfers_repo=TransfersRepository(
        transfers_ds=TransfersDataSource(),
    ),
)
