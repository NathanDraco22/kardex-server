from typing import Any, AsyncGenerator
from kardex.services.mongo_collections.v1 import InvoicesCollection


class InvoicesDataSource:
    async def create_invoice(self, invoice: dict[str, Any]) -> dict[str, Any]:
        collection = InvoicesCollection()
        await collection.create_invoice(invoice)
        return invoice

    async def get_all_invoices(self, **kargs) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_all_invoices(**kargs)

    async def get_all_product_sales(self, **kargs) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_all_product_sales(**kargs)

    def get_all_invoices_stream(self, **kargs) -> AsyncGenerator[dict[str, Any], None]:
        collection = InvoicesCollection()
        return collection.fetch_all_invoices_stream(**kargs)

    async def get_totals_from_invoices(self, **kargs) -> dict[str, Any]:
        collection = InvoicesCollection()
        return await collection.get_totals_from_invoices(**kargs)

    async def get_totals_invoices_by_payment_type(
        self, **kargs
    ) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.get_totals_from_invoices_by_payment_type(**kargs)

    async def get_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.fetch_invoice_by_id(invoice_id)

    async def get_invoice_by(
        self,
        client_id: str,
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_all_invoices_by(client_id, offset, limit)

    async def get_pending_to_paid_invoices(
        self, client_id: str
    ) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_pending_to_paid_invoices(client_id)

    async def get_invoice_by_doc_number(self, doc_number: str) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.fetch_invoice_by_doc_number(doc_number)

    async def update_invoice_by_id(
        self, invoice_id: str, invoice: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = InvoicesCollection()
        return await collection.update_invoice_by_id(invoice_id, invoice)

    async def get_invoice_history(self, **kargs) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.fetch_invoice_history(**kargs)

    async def get_invoice_resume(self, **kargs) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.get_invoice_resume(**kargs)

    async def get_pending_invoice_totals_by_branch(
        self, **kwargs
    ) -> list[dict[str, Any]]:
        collection = InvoicesCollection()
        return await collection.get_pending_invoice_totals_by_branch(**kwargs)
