from fastapi import APIRouter, Depends
from kardex.repos.v1.invoices import (
    CreateInvoice,
    UpdateInvoice,
    InvoiceInDb,
    InvoiceTotals,
    ProductSalesTotal,
)

from app_middleware import auth_middleware
from kardex.repos.v1.common.models.history_params import HistoryClientParams

from responses.v1 import ListResponse

from .invoices_controller import invoices_controller
from .responses import InvoiceResponse, InvoiceAnonResponse
from api.common.query_params import InvoiceQueryParams

invoices_router = APIRouter(
    tags=["invoicesV1"], dependencies=[Depends(auth_middleware)]
)


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


@invoices_router.get("/product-sales")
async def get_all_product_sales(
    query_params: InvoiceQueryParams = Depends(),
) -> ListResponse[ProductSalesTotal]:
    return await invoices_controller.get_all_product_sales(query_params)


@invoices_router.get("/totals")
async def get_totals_from_invoices(
    query_params: InvoiceQueryParams = Depends(),
) -> InvoiceTotals:
    return await invoices_controller.get_totals_from_invoices(query_params)


@invoices_router.get("/totals/byPaymentType")
async def get_totals_invoices_by_payment_type(
    query_params: InvoiceQueryParams = Depends(),
) -> ListResponse[InvoiceTotals]:
    return await invoices_controller.get_totals_invoices_by_payment_type(query_params)


@invoices_router.get("/history")
async def get_invoices_history(
    params: HistoryClientParams = Depends(),
) -> ListResponse[InvoiceInDb]:
    return await invoices_controller.get_invoice_history(params)


@invoices_router.get("/byProduct/{product_id}")
async def get_invoices_by_product(
    product_id: str,
    query_params: InvoiceQueryParams = Depends(),
) -> ListResponse[InvoiceInDb]:
    return await invoices_controller.get_invoices_by_product(product_id, query_params)


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
