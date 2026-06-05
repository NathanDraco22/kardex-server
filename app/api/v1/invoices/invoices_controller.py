from fastapi import HTTPException, status
from kardex.core.invoice_register.invoice_register import InvoiceRegister
from kardex.repos.v1.invoices import (
    CreateInvoice,
    UpdateInvoice,
    InvoiceInDb,
    InvoicesRepository,
    InvoicesDataSource,
    InvoiceTotals,
    ProductSalesTotal,
)
from responses.v1 import ListResponse
from kardex.repos.v1.common.models.history_params import HistoryClientParams


from .responses import InvoiceResponse, InvoiceAnonResponse
from kardex.repos.v1.common.filter_params import InvoiceFilterParams, TotalsFilterParams


class InvoicesController:
    def __init__(self, invoices_repo: InvoicesRepository) -> None:
        self.invoices_repo = invoices_repo
        self.invoices_regis = InvoiceRegister()

    async def create_invoice(self, body: CreateInvoice) -> InvoiceResponse:
        invoice, client_account = await self.invoices_regis.regis_invoice(body)
        return InvoiceResponse(
            invoice=invoice,
            clientAccount=client_account,
        )

    async def create_anon_invoice(self, body: CreateInvoice) -> InvoiceAnonResponse:
        invoice, _ = await self.invoices_regis.regis_anon_invoice(body)
        return InvoiceAnonResponse(invoice=invoice)

    async def get_all_invoices(
        self, query_params: InvoiceFilterParams
    ) -> ListResponse[InvoiceInDb]:
        invoices = await self.invoices_repo.get_all_invoices(query_params)
        return ListResponse(count=len(invoices), data=invoices)

    async def get_invoices_by_product(
        self, product_id: str, query_params: InvoiceFilterParams
    ) -> ListResponse[InvoiceInDb]:
        invoices = await self.invoices_repo.get_all_invoices_by_product(
            product_id, query_params
        )
        return ListResponse(count=len(invoices), data=invoices)

    async def get_all_product_sales(
        self, query_params: InvoiceFilterParams
    ) -> ListResponse[ProductSalesTotal]:
        product_sales = await self.invoices_repo.get_all_product_sales(query_params)
        return ListResponse(count=len(product_sales), data=product_sales)

    async def get_totals_from_invoices(
        self, query_params: InvoiceFilterParams
    ) -> InvoiceTotals:
        return await self.invoices_repo.get_totals_from_invoices(query_params)

    async def get_totals_invoices_by_payment_type(
        self, query_params: InvoiceFilterParams
    ) -> ListResponse[InvoiceTotals]:
        totals_params = TotalsFilterParams(
            branchId=query_params.branchId or "",
            startDate=query_params.startDate or 0,
            endDate=query_params.endDate or 0,
        )
        res = await self.invoices_repo.get_totals_invoices_by_payment_type(totals_params)
        return ListResponse(count=len(res), data=res)

    async def get_invoice_by_id(self, invoice_id: str) -> InvoiceInDb:
        invoice = await self.invoices_repo.get_invoice_by_id(invoice_id)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        return invoice

    async def get_invoice_by_doc_number(self, doc_number: str) -> InvoiceInDb:
        invoice = await self.invoices_repo.get_invoice_by_doc_number(doc_number)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        return invoice

    async def get_invoice_by(
        self,
        client_id: str,
        offset: int,
        limit: int,
    ) -> ListResponse[InvoiceInDb]:
        invoices = await self.invoices_repo.get_invoice_by(client_id, offset, limit)
        return ListResponse(count=len(invoices), data=invoices)

    async def get_pending_to_paid_invoices(
        self, client_id: str
    ) -> ListResponse[InvoiceInDb]:
        invoices = await self.invoices_repo.get_pending_to_paid_invoices(client_id)
        return ListResponse(count=len(invoices), data=invoices)

    async def update_invoice_by_id(
        self, invoice_id: str, body: UpdateInvoice
    ) -> InvoiceInDb:
        updated_invoice = await self.invoices_repo.update_invoice_by_id(
            invoice_id, body
        )
        if updated_invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        return updated_invoice

    async def get_invoice_history(
        self, params: HistoryClientParams
    ) -> ListResponse[InvoiceInDb]:
        invoices = await self.invoices_repo.get_invoice_history(params)
        return ListResponse(count=len(invoices), data=invoices)


invoices_controller = InvoicesController(
    invoices_repo=InvoicesRepository(
        invoices_ds=InvoicesDataSource(),
    ),
)
