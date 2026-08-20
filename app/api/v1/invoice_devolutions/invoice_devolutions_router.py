from fastapi import APIRouter, Depends

from app_middleware import auth_middleware

from .invoice_devolutions_controller import invoice_devolutions_controller
from .responses import InvoiceDevolutionsResponse


invoice_devolutions_router = APIRouter(
    tags=["invoice_devolutionsV1"], dependencies=[Depends(auth_middleware)]
)


@invoice_devolutions_router.get("/invoice-doc-number/{invoice_doc_number}")
async def get_invoice_devolutions_by_doc_number(
    invoice_doc_number: str,
) -> InvoiceDevolutionsResponse:
    return await invoice_devolutions_controller.get_invoice_devolutions_by_doc_number(
        invoice_doc_number
    )


@invoice_devolutions_router.get("/anon-invoice-doc-number/{invoice_doc_number}")
async def get_anon_invoice_devolutions_by_doc_number(
    invoice_doc_number: str,
) -> InvoiceDevolutionsResponse:
    return (
        await invoice_devolutions_controller.get_anon_invoice_devolutions_by_doc_number(
            invoice_doc_number
        )
    )


@invoice_devolutions_router.get("/{invoice_id}")
async def get_invoice_devolutions_by_id(
    invoice_id: str,
) -> InvoiceDevolutionsResponse:
    return await invoice_devolutions_controller.get_invoice_devolutions_by_id(
        invoice_id
    )
