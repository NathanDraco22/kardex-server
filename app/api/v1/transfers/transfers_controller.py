from fastapi import HTTPException, status, BackgroundTasks

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
from repos.v1.expiration_logs import (
    ExpirationLogsRepository,
    ExpirationLogsDataSource,
    CreateExpirationLog,
    ProductInfo,
)

from .query_params import TransferQueryParams


class TransfersController:
    def __init__(
        self,
        transfers_repo: TransfersRepository,
        expiration_logs_repo: ExpirationLogsRepository,
    ) -> None:
        self.transfers_repo = transfers_repo
        self.expiration_logs_repo = expiration_logs_repo
        self.transfer_manager = TransferManager()

    async def _regis_log(self, transfer: TransferInDb) -> None:
        try:
            new_logs: list[CreateExpirationLog] = []
            for item in transfer.items:
                expiration_date = item.expirationDate
                if expiration_date is None:
                    continue
                new_product_info = ProductInfo(
                    id=item.id,
                    name=item.name,
                    brandName=item.brandName,
                    categoryName=item.categoryName,
                    code=item.code,
                    unitName=item.unitName,
                )

                new_expiration_log = CreateExpirationLog(
                    product=new_product_info,
                    branchId=transfer.destination,
                    expirationDate=expiration_date,
                )

                new_logs.append(new_expiration_log)

            await self.expiration_logs_repo.create_many_expiration_logs(new_logs)

        except Exception as e:
            print(e)

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
        self, transfer_id: str, intent: ReceiveTransferIntent, bg_tasks: BackgroundTasks
    ) -> TransferInDb:
        transfer, _ = await self.transfer_manager.regis_incoming_transfer(
            transfer_id, intent
        )

        bg_tasks.add_task(self._regis_log, transfer)

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
    expiration_logs_repo=ExpirationLogsRepository(
        expiration_logs_ds=ExpirationLogsDataSource(),
    ),
)
