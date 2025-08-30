from fastapi import APIRouter

from repos.v1.receipts import CreateReceipt, UpdateReceipt, ReceiptInDb

from .receipts_controller import receipts_controller


receipts_router = APIRouter(tags=["receiptsV1"])


@receipts_router.post("")
async def create_receipt(body: CreateReceipt) -> ReceiptInDb:
    return await receipts_controller.create_receipt(body)


@receipts_router.get("")
async def get_all_receipts() -> list[ReceiptInDb]:
    return await receipts_controller.get_all_receipts()


@receipts_router.get("/{receipt_id}")
async def get_receipt_by_id(receipt_id: str) -> ReceiptInDb:
    return await receipts_controller.get_receipt_by_id(receipt_id)


@receipts_router.patch("/{receipt_id}")
async def update_receipt_by_id(receipt_id: str, body: UpdateReceipt) -> ReceiptInDb: 
    return await receipts_controller.update_receipt_by_id(receipt_id, body)


@receipts_router.delete("/{receipt_id}")
async def delete_receipt_by_id(receipt_id: str) -> ReceiptInDb:
    return await receipts_controller.delete_receipt_by_id(receipt_id)
