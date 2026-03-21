from typing import AsyncGenerator
from repos.v1.common.models.history_params import HistoryClientParams
from .data.invoices_datasource import InvoicesDataSource
from .models.invoice_model import UpdateInvoice, InvoiceInDb
from .models.invoice_totals_model import InvoiceTotals
from repos.v1.common.models.invoice_product_sale import ProductSalesTotal
from repos.v1.invoices.models.invoice_summary import BranchPortfolioSummary


class InvoicesRepository:
    def __init__(self, invoices_ds: InvoicesDataSource):
        self.invoices_ds = invoices_ds

    async def get_all_invoices(self, **kargs) -> list[InvoiceInDb]:
        results = await self.invoices_ds.get_all_invoices(**kargs)
        models = [InvoiceInDb.model_validate(result) for result in results]
        return models

    async def get_all_product_sales(self, **kargs) -> list[ProductSalesTotal]:
        results = await self.invoices_ds.get_all_product_sales(**kargs)
        models = [ProductSalesTotal.model_validate(result) for result in results]
        return models

    async def get_all_invoices_stream(
        self, **kargs
    ) -> AsyncGenerator[InvoiceInDb, None]:
        async for result in self.invoices_ds.get_all_invoices_stream(**kargs):
            yield InvoiceInDb.model_validate(result)

    async def get_totals_from_invoices(self, **kargs) -> InvoiceTotals:
        res = await self.invoices_ds.get_totals_from_invoices(**kargs)
        return InvoiceTotals(**res)

    async def get_totals_invoices_by_payment_type(self, **kargs) -> list[InvoiceTotals]:
        res = await self.invoices_ds.get_totals_invoices_by_payment_type(**kargs)
        return [InvoiceTotals(**result) for result in res]

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

    async def get_invoice_history(
        self, params: HistoryClientParams
    ) -> list[InvoiceInDb]:
        params_data = params.to_query_params()
        results = await self.invoices_ds.get_invoice_history(**params_data)
        models = [InvoiceInDb.model_validate(result) for result in results]
        return models

    async def get_invoice_summary(self, **kwargs) -> list[BranchPortfolioSummary]:
        result = await self.invoices_ds.get_invoice_resume(**kwargs)

        models = [BranchPortfolioSummary.model_validate(result) for result in result]

        return models
