from fastapi import APIRouter, Depends

from kardex.repos.v1.orders import CreateOrder, UpdateOrder, OrderInDb
from kardex.repos.v1.common.models.invoice_product_sale import ProductSalesTotal
from kardex.repos.v1.common.models import ProductStockDemand
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .orders_controller import orders_controller
from .responses import ConvertOrderToInvoiceResponse
from .orders_query_params import OrderQueryParams


orders_router = APIRouter(
    tags=["ordersV1"],
    dependencies=[Depends(auth_middleware)],
)


@orders_router.post("")
async def create_order(body: CreateOrder) -> OrderInDb:
    return await orders_controller.create_order(body)


@orders_router.post("/make-invoice/{order_id}")
async def convert_order_to_invoice(order_id: str) -> ConvertOrderToInvoiceResponse:
    invoice, order = await orders_controller.convert_order_to_invoice(order_id)
    return ConvertOrderToInvoiceResponse(invoice=invoice, order=order)


@orders_router.get("")
async def get_paginated_orders(
    query_params: OrderQueryParams = Depends(),
) -> ListResponse[OrderInDb]:
    return await orders_controller.get_paginated_orders(query_params)


@orders_router.get("/product-orders")
async def get_product_in_orders(
    query_params: OrderQueryParams = Depends(),
) -> ListResponse[ProductSalesTotal]:
    return await orders_controller.get_product_in_orders(query_params)


@orders_router.get("/product-demand-vs-inventory")
async def get_product_demand_vs_inventory(
    query_params: OrderQueryParams = Depends(),
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
