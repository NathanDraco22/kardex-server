from fastapi import HTTPException, status
from kardex.repos.v1.invoices import InvoicesRepository, InvoicesDataSource
from kardex.repos.v1.devolutions import DevolutionsRepository, DevolutionsDataSource

from kardex.core.default_values.create_default_client import SALE_CLIENT_ID

from .responses import InvoiceDevolutionsResponse


class InvoiceDevolutionsController:
    def __init__(self) -> None:
        self.invoices_repo = InvoicesRepository(
            invoices_ds=InvoicesDataSource(),
        )
        self.devolutions_repo = DevolutionsRepository(
            devolutions_ds=DevolutionsDataSource(),
        )

    async def get_invoice_devolutions_by_doc_number(
        self, invoice_doc_number: str
    ) -> InvoiceDevolutionsResponse:
        invoice = await self.invoices_repo.get_invoice_by_doc_number(invoice_doc_number)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        devolutions = await self.devolutions_repo.get_devolution_by_invoice_id(
            invoice.id, None
        )
        return InvoiceDevolutionsResponse(
            invoice=invoice,
            devolutions=devolutions,
        )

    async def get_anon_invoice_devolutions_by_doc_number(
        self, invoice_doc_number: str
    ) -> InvoiceDevolutionsResponse:
        invoice = await self.invoices_repo.get_invoice_by_doc_number(invoice_doc_number)

        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        if invoice.clientId != SALE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        devolutions = await self.devolutions_repo.get_devolution_by_invoice_id(
            invoice.id, SALE_CLIENT_ID
        )

        return InvoiceDevolutionsResponse(
            invoice=invoice,
            devolutions=devolutions,
        )


invoice_devolutions_controller = InvoiceDevolutionsController()
