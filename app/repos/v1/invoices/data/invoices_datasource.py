from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import InvoicesCollection


class InvoicesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_invoice(self, invoice: dict[str, Any]) -> dict[str, Any]:
        collection = InvoicesCollection()
        await collection.create_invoice(invoice)
        return invoice

    async def get_all_invoices(self) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_all_invoices()

    async def get_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.fetch_invoice_by_id(invoice_id)

    async def get_invoice_by_doc_number(self, doc_number: str):
        collection = InvoicesCollection()
        return await collection.fetch_invoice_by_doc_number(doc_number)

    async def update_invoice_by_id(
        self, invoice_id: str, invoice: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.update_invoice_by_id(invoice_id, invoice)

    async def delete_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.delete_invoice_by_id(invoice_id)
