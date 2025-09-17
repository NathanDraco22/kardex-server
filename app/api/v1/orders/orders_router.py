from fastapi import APIRouter

from repos.v1.orders import CreateOrder, UpdateOrder, OrderInDb
from responses.v1 import ListResponse


from .orders_controller import orders_controller


orders_router = APIRouter(tags=["ordersV1"])


@orders_router.post("")
async def create_order(body: CreateOrder) -> OrderInDb:
    return await orders_controller.create_order(body)


@orders_router.get("")
async def get_paginated_orders(
    skip: int,
    limit: int,
    client_id: str | None = None,
    branch_id: str | None = None,
) -> ListResponse[OrderInDb]:
    return await orders_controller.get_paginated_orders(
        skip,
        limit,
        client_id,
        branch_id,
    )


@orders_router.get("/{order_id}")
async def get_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.get_order_by_id(order_id)


@orders_router.patch("/{order_id}")
async def update_order_by_id(order_id: str, body: UpdateOrder) -> OrderInDb:
    return await orders_controller.update_order_by_id(order_id, body)


@orders_router.patch("cancel/{order_id}")
async def cancel_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.cancel_order_by_id(order_id)
