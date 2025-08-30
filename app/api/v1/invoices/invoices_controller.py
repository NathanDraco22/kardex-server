from fastapi import HTTPException, status

from core.invoice_register.invoice_register import InvoiceRegister

from repos.v1.invoices import (
    CreateInvoice,
    UpdateInvoice,
    InvoiceInDb,
    InvoicesRepository,
    InvoicesDataSource,
)

from .responses import InvoiceResponse


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

    async def get_all_invoices(self) -> list[InvoiceInDb]:
        invoices = await self.invoices_repo.get_all_invoices()
        return invoices

    async def get_invoice_by_id(self, invoice_id: str) -> InvoiceInDb:
        invoice = await self.invoices_repo.get_invoice_by_id(invoice_id)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        return invoice

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

    async def delete_invoice_by_id(self, invoice_id: str) -> InvoiceInDb:
        deleted_invoice = await self.invoices_repo.delete_invoice_by_id(invoice_id)
        if deleted_invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        return deleted_invoice


invoices_controller = InvoicesController(
    invoices_repo=InvoicesRepository(
        invoices_ds=InvoicesDataSource(),
    ),
)
