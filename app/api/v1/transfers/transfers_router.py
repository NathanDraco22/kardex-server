from fastapi import APIRouter, Depends, BackgroundTasks
from kardex.repos.v1.transfers import (
    CreateTransfer,
    TransferInDb,
    ReceiveTransferIntent,
    CancelTransferIntent,
)
from app_middleware import auth_middleware
from responses.v1 import ListResponse

from .transfers_controller import transfers_controller
from kardex.repos.v1.common.filter_params import TransferFilterParams


transfers_router = APIRouter(
    tags=["transfersV1"], dependencies=[Depends(auth_middleware)]
)


@transfers_router.post("")
async def create_transfer(body: CreateTransfer) -> TransferInDb:
    return await transfers_controller.create_transfer(body)


@transfers_router.get("")
async def get_all_transfers(
    query: TransferFilterParams = Depends(),
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
    transfer_id: str, intent: ReceiveTransferIntent, bg_tasks: BackgroundTasks
) -> TransferInDb:
    return await transfers_controller.receive_transfer(transfer_id, intent, bg_tasks)


@transfers_router.post("/{transfer_id}/cancel")
async def cancel_transfer(
    transfer_id: str, intent: CancelTransferIntent
) -> TransferInDb:
    return await transfers_controller.cancel_transfer(transfer_id, intent)
