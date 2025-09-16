from fastapi import HTTPException, status


from core.receipt_register.receipt_register import ReceiptRegister
from repos.v1.receipts import (
    CreateReceipt,
    UpdateReceipt,
    ReceiptInDb,
    ReceiptsRepository,
    ReceiptsDataSource,
)


class ReceiptsController:
    def __init__(self, receipts_repo: ReceiptsRepository) -> None:
        self.receipts_repo = receipts_repo
        self.receipt_register = ReceiptRegister()

    async def create_receipt(self, body: CreateReceipt) -> ReceiptInDb:
        receipt, _ = await self.receipt_register.regis_receipt(body)
        return receipt

    async def get_all_receipts(self) -> list[ReceiptInDb]:
        receipts = await self.receipts_repo.get_all_receipts()
        return receipts

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
        deleted_receipt = await self.receipts_repo.delete_receipt_by_id(receipt_id)
        if deleted_receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return deleted_receipt


receipts_controller = ReceiptsController(
    receipts_repo=ReceiptsRepository(
        receipts_ds=ReceiptsDataSource(),
    ),
)
