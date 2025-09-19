from .data.invoices_datasource import InvoicesDataSource
from .models.invoice_model import UpdateInvoice, InvoiceInDb


class InvoicesRepository:
    def __init__(self, invoices_ds: InvoicesDataSource):
        self.invoices_ds = invoices_ds

    async def get_all_invoices(self, **kargs) -> list[InvoiceInDb]:
        results = await self.invoices_ds.get_all_invoices(**kargs)
        models = [InvoiceInDb.model_validate(result) for result in results]
        return models

    async def get_invoice_by_id(self, invoice_id: str) -> InvoiceInDb | None:
        result = await self.invoices_ds.get_invoice_by_id(invoice_id)

        if result is None:
            return None

        return InvoiceInDb.model_validate(result)

    async def get_invoice_by_doc_number(self, doc_number: str) -> InvoiceInDb | None:
        result = await self.invoices_ds.get_invoice_by_doc_number(doc_number)

        if result is None:
            return None

        return InvoiceInDb.model_validate(result)

    async def get_invoice_by(
        self, client_id: str, offset: int, limit: int
    ) -> list[InvoiceInDb]:
        results = await self.invoices_ds.get_invoice_by(client_id, offset, limit)
        models = [InvoiceInDb.model_validate(result) for result in results]
        return models

    async def get_pending_to_paid_invoices(self, client_id: str) -> list[InvoiceInDb]:
        results = await self.invoices_ds.get_pending_to_paid_invoices(client_id)
        models = [InvoiceInDb.model_validate(result) for result in results]
        return models

    async def update_invoice_by_id(
        self, invoice_id: str, invoice: UpdateInvoice
    ) -> InvoiceInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_invoice_by_id(self, invoice_id: str) -> InvoiceInDb | None:
        result = await self.invoices_ds.delete_invoice_by_id(invoice_id)

        if result is None:
            return None

        return InvoiceInDb.model_validate(result)
