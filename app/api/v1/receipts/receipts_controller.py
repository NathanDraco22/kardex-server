from fastapi import HTTPException, status


from kardex.core.receipt_register.receipt_register import ReceiptRegister
from kardex.repos.v1.receipts import (
    CreateReceipt,
    UpdateReceipt,
    ReceiptInDb,
    ReceiptsRepository,
    ReceiptsDataSource,
    ReceiptTotal,
)
from kardex.repos.v1.common.models.history_params import HistoryClientParams


from .query_params import ReceiptQueryParams
from responses.v1 import ListResponse


class ReceiptsController:
    def __init__(self, receipts_repo: ReceiptsRepository) -> None:
        self.receipts_repo = receipts_repo
        self.receipt_register = ReceiptRegister()

    async def create_receipt(self, body: CreateReceipt) -> ReceiptInDb:
        receipt, _ = await self.receipt_register.regis_receipt(body)
        return receipt

    async def get_all_receipts(
        self, query_params: ReceiptQueryParams
    ) -> ListResponse[ReceiptInDb]:
        if query_params.endDate is None or query_params.startDate is None:
            query_params.startDate = None
            query_params.endDate = None

        receipts = await self.receipts_repo.get_all_receipts(
            **query_params.model_dump(exclude_none=True)
        )

        return ListResponse(
            count=len(receipts),
            data=receipts,
        )

    async def get_receipts_by_invoice_id(
        self, invoice_id: str
    ) -> ListResponse[ReceiptInDb]:
        receipts = await self.receipts_repo.get_receipts_by_invoice_id(invoice_id)
        return ListResponse(
            count=len(receipts),
            data=receipts,
        )

    async def get_totals_from_receipts(
        self, query_params: ReceiptQueryParams
    ) -> ReceiptTotal:
        if query_params.endDate is None or query_params.startDate is None:
            query_params.startDate = None
            query_params.endDate = None
        return await self.receipts_repo.get_totals_from_receipts(
            **query_params.model_dump()
        )

    async def get_totals_from_receipts_by_payment_method(
        self, query_params: ReceiptQueryParams
    ) -> ListResponse[ReceiptTotal]:
        if query_params.endDate is None or query_params.startDate is None:
            query_params.startDate = None
            query_params.endDate = None

        kwargs = query_params.model_dump(exclude_none=True)

        kwargs.pop("offset", None)
        kwargs.pop("limit", None)

        res = await self.receipts_repo.get_totals_from_receipts_by_payment_method(
            **kwargs
        )

        return ListResponse(count=len(res), data=res)

    async def get_receipt_by_id(self, receipt_id: str) -> ReceiptInDb:
        receipt = await self.receipts_repo.get_receipt_by_id(receipt_id)
        if receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return receipt

    async def update_receipt_by_id(
        self,
        receipt_id: str,
        body: UpdateReceipt,
    ) -> ReceiptInDb:
        updated_receipt = await self.receipts_repo.update_receipt_by_id(
            receipt_id, body
        )
        if updated_receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return updated_receipt

    async def delete_receipt_by_id(self, receipt_id: str) -> ReceiptInDb:
        deleted_receipt, _ = await self.receipt_register.delete_receipt(receipt_id)
        return deleted_receipt

    async def get_receipt_history(
        self, query_params: HistoryClientParams
    ) -> ListResponse[ReceiptInDb]:
        receipts = await self.receipts_repo.get_receipt_history(query_params)
        return ListResponse(
            count=len(receipts),
            data=receipts,
        )

    async def get_receipt_by_doc_number(self, doc_number: str) -> ReceiptInDb:
        receipt = await self.receipts_repo.get_receipt_by_doc_number(doc_number)
        if receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return receipt


receipts_controller = ReceiptsController(
    receipts_repo=ReceiptsRepository(
        receipts_ds=ReceiptsDataSource(),
    ),
)
