from fastapi import HTTPException, status

from repos.v1.invoices.models.invoice_model import InvoiceInDb, CreateInvoice
from core.order_register.order_register import OrderRegister
from core.invoice_register.invoice_register import InvoiceRegister
from core.order_register.cancel_order import cancel_order
from repos.v1.orders import (
    CreateOrder,
    UpdateOrder,
    OrderInDb,
    OrdersRepository,
    OrdersDataSource,
)

from responses.v1 import ListResponse


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo
        self.order_register = OrderRegister()
        self.invoice_register = InvoiceRegister()

    async def create_order(self, body: CreateOrder) -> OrderInDb:
        res, _ = await self.order_register.regis_order(body)
        return res

    async def convert_order_to_invoice(
        self, order_id: str
    ) -> tuple[InvoiceInDb, OrderInDb]:
        order = await self.orders_repo.get_order_by_id(order_id)

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not open",
            )

        create_invoice = CreateInvoice(
            branchId=order.branchId,
            clientId=order.clientId,
            clientInfo=order.clientInfo,
            orderNumber=order.docNumber,
            saleItems=order.saleItems,
            description=order.description,
            amountPaid=order.amountPaid,
            totalCost=order.totalCost,
            paymentType=order.paymentType,
            status="open",
            total=order.total,
        )

        res, _ = await self.invoice_register.regis_invoice(create_invoice)
        order = await self.orders_repo.get_order_by_id(order_id)

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        return res, order

    async def get_paginated_orders(
        self,
        skip: int,
        limit: int,
        client_id: str | None,
        branch_id: str | None,
    ) -> ListResponse[OrderInDb]:
        res = await self.orders_repo.get_paginated_orders(
            skip,
            limit,
            client_id,
            branch_id,
        )
        return ListResponse(
            count=len(res),
            data=res,
        )

    async def get_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return order

    async def update_order_by_id(self, order_id: str, body: UpdateOrder) -> OrderInDb:
        updated_order = await self.orders_repo.update_order_by_id(order_id, body)
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated_order

    async def cancel_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not open",
            )

        cancelled_order = await cancel_order(order)

        return cancelled_order


orders_controller = OrdersController(
    orders_repo=OrdersRepository(
        orders_ds=OrdersDataSource(),
    ),
)
