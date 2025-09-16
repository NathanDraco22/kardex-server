from .data.receipts_datasource import ReceiptsDataSource
from .models.receipt_model import CreateReceipt, UpdateReceipt, ReceiptInDb


class ReceiptsRepository:
    def __init__(self, receipts_ds: ReceiptsDataSource):
        self.receipts_ds = receipts_ds

    async def create_receipt(self, create_receipt: CreateReceipt) -> ReceiptInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_receipts(self) -> list[ReceiptInDb]:
        results = await self.receipts_ds.get_all_receipts()
        models = [ReceiptInDb.model_validate(result) for result in results]
        return models

    async def get_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.get_receipt_by_id(receipt_id)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)

    async def get_receipt_by_doc_number(self, doc_number: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.get_receipt_by_doc_number(doc_number)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)

    async def update_receipt_by_id(
        self, receipt_id: str, receipt: UpdateReceipt
    ) -> ReceiptInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.delete_receipt_by_id(receipt_id)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)
