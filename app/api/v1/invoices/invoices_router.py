from fastapi import APIRouter

from repos.v1.invoices import CreateInvoice, UpdateInvoice, InvoiceInDb

from .invoices_controller import invoices_controller
from .responses import InvoiceResponse


invoices_router = APIRouter(tags=["invoicesV1"])


@invoices_router.post("")
async def create_invoice(body: CreateInvoice) -> InvoiceResponse:
    return await invoices_controller.create_invoice(body)


@invoices_router.get("")
async def get_all_invoices() -> list[InvoiceInDb]:
    return await invoices_controller.get_all_invoices()


@invoices_router.get("/{invoice_id}")
async def get_invoice_by_id(invoice_id: str) -> InvoiceInDb:
    return await invoices_controller.get_invoice_by_id(invoice_id)


@invoices_router.patch("/{invoice_id}")
async def update_invoice_by_id(invoice_id: str, body: UpdateInvoice) -> InvoiceInDb:
    return await invoices_controller.update_invoice_by_id(invoice_id, body)


@invoices_router.delete("/{invoice_id}")
async def delete_invoice_by_id(invoice_id: str) -> InvoiceInDb:
    return await invoices_controller.delete_invoice_by_id(invoice_id)
