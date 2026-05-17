from fastapi import APIRouter, Depends

from kardex.repos.v1.receipts import CreateReceipt, UpdateReceipt, ReceiptInDb, ReceiptTotal
from kardex.repos.v1.common.models.history_params import HistoryClientParams
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .receipts_controller import receipts_controller

from .query_params import ReceiptQueryParams


receipts_router = APIRouter(
    tags=["receiptsV1"],
    dependencies=[Depends(auth_middleware)],
)


@receipts_router.post("")
async def create_receipt(body: CreateReceipt) -> ReceiptInDb:
    return await receipts_controller.create_receipt(body)


@receipts_router.get("")
async def get_all_receipts(
    query_params: ReceiptQueryParams = Depends(),
) -> ListResponse[ReceiptInDb]:
    return await receipts_controller.get_all_receipts(query_params)


@receipts_router.get("/invoice/{invoice_id}")
async def get_receipts_by_invoice_id(invoice_id: str) -> ListResponse[ReceiptInDb]:
    return await receipts_controller.get_receipts_by_invoice_id(invoice_id)


@receipts_router.get("/totals")
async def get_totals_from_receipts(
    query_params: ReceiptQueryParams = Depends(),
) -> ReceiptTotal:
    return await receipts_controller.get_totals_from_receipts(query_params)


@receipts_router.get("/totals/byPaymentMethod")
async def get_totals_from_receipts_by_payment_method(
    query_params: ReceiptQueryParams = Depends(),
) -> ListResponse[ReceiptTotal]:
    return await receipts_controller.get_totals_from_receipts_by_payment_method(
        query_params
    )


@receipts_router.get("/history")
async def get_receipt_history(
    query_params: HistoryClientParams = Depends(),
) -> ListResponse[ReceiptInDb]:
    return await receipts_controller.get_receipt_history(query_params)


@receipts_router.get("/doc/{doc_number}")
async def get_receipt_by_doc_number(doc_number: str) -> ReceiptInDb:
    return await receipts_controller.get_receipt_by_doc_number(doc_number)


@receipts_router.get("/{receipt_id}")
async def get_receipt_by_id(receipt_id: str) -> ReceiptInDb:
    return await receipts_controller.get_receipt_by_id(receipt_id)


@receipts_router.patch("/{receipt_id}")
async def update_receipt_by_id(receipt_id: str, body: UpdateReceipt) -> ReceiptInDb:
    return await receipts_controller.update_receipt_by_id(receipt_id, body)


@receipts_router.delete("/{receipt_id}")
async def delete_receipt_by_id(receipt_id: str) -> ReceiptInDb:
    return await receipts_controller.delete_receipt_by_id(receipt_id)
