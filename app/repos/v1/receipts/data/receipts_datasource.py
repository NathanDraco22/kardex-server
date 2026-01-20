from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ReceiptsCollection


class ReceiptsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        collection = ReceiptsCollection()
        await collection.create_receipt(receipt)
        return receipt

    async def get_all_receipts(self, **kwargs) -> list[dict[str, Any]]:
        collection = ReceiptsCollection()
        return await collection.fetch_all_receipts(**kwargs)

    async def get_receipts_by_invoice_id(self, invoice_id: str) -> list[dict[str, Any]]:
        collection = ReceiptsCollection()
        return await collection.fetch_receipts_by_invoice_id(invoice_id)

    async def get_totals_from_receipts(self, **kwargs) -> dict[str, Any]:
        collection = ReceiptsCollection()
        return await collection.get_totals_from_receipts(**kwargs)

    async def get_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = ReceiptsCollection()
        return await collection.fetch_receipt_by_id(receipt_id)

    async def get_receipt_by_doc_number(self, docNumber: str) -> dict[str, Any] | None:
        collection = ReceiptsCollection()
        return await collection.fetch_receipt_by_doc_number(docNumber)

    async def update_receipt_by_id(
        self, receipt_id: str, receipt: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ReceiptsCollection()
        return await collection.update_receipt_by_id(receipt_id, receipt)

    async def delete_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = ReceiptsCollection()
        return await collection.delete_receipt_by_id(receipt_id)

    async def fetch_receipt_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = ReceiptsCollection()
        return await collection.fetch_receipt_history(**kwargs)
