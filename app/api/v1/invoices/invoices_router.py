from fastapi import APIRouter, Depends

from repos.v1.invoices import (
    CreateInvoice,
    UpdateInvoice,
    InvoiceInDb,
    InvoiceTotals,
)

from responses.v1 import ListResponse

from .invoices_controller import invoices_controller
from .responses import InvoiceResponse, InvoiceAnonResponse
from .query_params import InvoiceQueryParams

invoices_router = APIRouter(tags=["invoicesV1"])


@invoices_router.post("")
async def create_invoice(body: CreateInvoice) -> InvoiceResponse:
    return await invoices_controller.create_invoice(body)


@invoices_router.post("/anon")
async def create_anon_invoice(body: CreateInvoice) -> InvoiceAnonResponse:
    return await invoices_controller.create_anon_invoice(body)


@invoices_router.get("")
async def get_all_invoices(
    query_params: InvoiceQueryParams = Depends(),
) -> ListResponse[InvoiceInDb]:
    return await invoices_controller.get_all_invoices(query_params)


@invoices_router.get("/totals")
async def get_totals_from_invoices(
    query_params: InvoiceQueryParams = Depends(),
) -> InvoiceTotals:
    return await invoices_controller.get_totals_from_invoices(query_params)


@invoices_router.get("/{invoice_id}")
async def get_invoice_by_id(invoice_id: str) -> InvoiceInDb:
    return await invoices_controller.get_invoice_by_id(invoice_id)


@invoices_router.get("/doc/{doc_number}")
async def get_invoice_by_doc_number(doc_number: str) -> InvoiceInDb:
    return await invoices_controller.get_invoice_by_doc_number(doc_number)


@invoices_router.get("/client/{client_id}")
async def get_invoice_by(
    client_id: str,
    offset: int = 0,
    limit: int = 25,
) -> ListResponse[InvoiceInDb]:
    return await invoices_controller.get_invoice_by(
        client_id,
        offset,
        limit,
    )


@invoices_router.get("/pending/{client_id}")
async def get_pending_to_paid_invoices(client_id: str) -> ListResponse[InvoiceInDb]:
    return await invoices_controller.get_pending_to_paid_invoices(client_id)


@invoices_router.patch("/{invoice_id}")
async def update_invoice_by_id(invoice_id: str, body: UpdateInvoice) -> InvoiceInDb:
    return await invoices_controller.update_invoice_by_id(invoice_id, body)


@invoices_router.delete("/{invoice_id}")
async def delete_invoice_by_id(invoice_id: str) -> InvoiceInDb:
    return await invoices_controller.delete_invoice_by_id(invoice_id)
