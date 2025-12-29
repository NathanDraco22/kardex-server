from fastapi import APIRouter, Depends

from repos.v1.transfers import (
    CreateTransfer,
    TransferInDb,
    ReceiveTransferIntent,
    CancelTransferIntent,
)

from responses.v1 import ListResponse

from .transfers_controller import transfers_controller
from .query_params import TransferQueryParams


transfers_router = APIRouter(tags=["transfersV1"])


@transfers_router.post("")
async def create_transfer(body: CreateTransfer) -> TransferInDb:
    return await transfers_controller.create_transfer(body)


@transfers_router.get("")
async def get_all_transfers(
    query: TransferQueryParams = Depends(),
) -> ListResponse[TransferInDb]:
    return await transfers_controller.get_all_transfers(query)


@transfers_router.get("/doc-number/{doc_number}")
async def get_transfer_by_doc_number(doc_number: str) -> TransferInDb:
    return await transfers_controller.get_transfer_by_doc_number(doc_number)


@transfers_router.get("/{transfer_id}")
async def get_transfer_by_id(transfer_id: str) -> TransferInDb:
    return await transfers_controller.get_transfer_by_id(transfer_id)


@transfers_router.post("/{transfer_id}/receive")
async def receive_transfer(
    transfer_id: str, intent: ReceiveTransferIntent
) -> TransferInDb:
    return await transfers_controller.receive_transfer(transfer_id, intent)


@transfers_router.post("/{transfer_id}/cancel")
async def cancel_transfer(
    transfer_id: str, intent: CancelTransferIntent
) -> TransferInDb:
    return await transfers_controller.cancel_transfer(transfer_id, intent)
