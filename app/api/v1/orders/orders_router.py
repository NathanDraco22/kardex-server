from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from kardex.repos.v1.orders import CreateOrder, UpdateOrder, OrderInDb
from kardex.repos.v1.common.models import ProductStockDemand, PaymentDetail, PaymentType
from kardex.repos.v1.common.models.invoice_product_sale import ProductSalesTotal
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .orders_controller import orders_controller
from .responses import ConvertOrderToInvoiceResponse
from kardex.repos.v1.common.filter_params import OrderFilterParams


orders_router = APIRouter(
    tags=["ordersV1"],
    dependencies=[Depends(auth_middleware)],
)


@orders_router.post("")
async def create_order(body: CreateOrder) -> OrderInDb:
    return await orders_controller.create_order(body)


class ConvertOrderToInvoiceRequest(BaseModel):
    shiftId: str | None = None
    paymentType: PaymentType | None = None
    bankReference: str | None = None
    paymentDetail: PaymentDetail | None = None


@orders_router.post("/make-invoice/{order_id}")
async def convert_order_to_invoice(
    order_id: str,
    req: Request,
    body: ConvertOrderToInvoiceRequest | None = None,
) -> ConvertOrderToInvoiceResponse:
    invoice, order = await orders_controller.convert_order_to_invoice(
        order_id,
        invoiced_by_user_id=getattr(req.state, "auth_user_id", None),
        invoiced_by_username=getattr(req.state, "auth_username", None),
        shift_id=body.shiftId if body is not None else None,
        payment_type=body.paymentType if body is not None else None,
        bank_reference=body.bankReference if body is not None else None,
        payment_detail=body.paymentDetail if body is not None else None,
    )
    return ConvertOrderToInvoiceResponse(invoice=invoice, order=order)


@orders_router.get("")
async def get_paginated_orders(
    query_params: OrderFilterParams = Depends(),
) -> ListResponse[OrderInDb]:
    return await orders_controller.get_paginated_orders(query_params)


@orders_router.get("/product-orders")
async def get_product_in_orders(
    query_params: OrderFilterParams = Depends(),
) -> ListResponse[ProductSalesTotal]:
    return await orders_controller.get_product_in_orders(query_params)


@orders_router.get("/product-demand-vs-inventory")
async def get_product_demand_vs_inventory(
    query_params: OrderFilterParams = Depends(),
) -> ListResponse[ProductStockDemand]:
    return await orders_controller.get_product_demand_vs_inventory(query_params)


@orders_router.get("/{order_id}")
async def get_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.get_order_by_id(order_id)


@orders_router.patch("/{order_id}")
async def update_order_draft_by_id(order_id: str, body: UpdateOrder) -> OrderInDb:
    return await orders_controller.update_order_draft_by_id(order_id, body)


@orders_router.patch("/cancel/{order_id}")
async def cancel_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.cancel_order_by_id(order_id)


@orders_router.delete("/draft/{order_id}")
async def delete_order_draft_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.delete_order_draft_by_id(order_id)
