from fastapi import HTTPException, status

from repos.v1.invoices.models.invoice_model import (
    InvoiceInDb,
    CreateInvoice,
    InvoiceStatus,
)
from core.order_register.order_register import OrderRegister
from core.invoice_register.invoice_register import InvoiceRegister
from core.order_register.cancel_order import cancel_order
from core.counter_manager.counter_manager import CounterManager
from repos.v1.orders import (
    CreateOrder,
    UpdateOrder,
    OrderInDb,
    OrdersRepository,
    OrdersDataSource,
)

from responses.v1 import ListResponse
from .orders_query_params import OrderQueryParams


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo
        self.order_register = OrderRegister()
        self.invoice_register = InvoiceRegister()

    async def create_order(self, body: CreateOrder) -> OrderInDb:
        if body.status == "draft":
            body.docNumber = await CounterManager().next_order_number()

            current_order = await self.orders_repo.get_order_by_doc_number(
                body.docNumber
            )
            if current_order is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Order with this document number already exists",
                )

            await self.order_register.validate_document(body)
            return await self.orders_repo.create_draft_order(body)
        else:
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

        allowed_statuses = ["open", "draft"]

        if order.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not open",
            )

        new_invoice_status: InvoiceStatus = "open"

        if order.status == "draft":
            new_invoice_status = "draft"

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
            status=new_invoice_status,
            total=order.total,
            createdBy=order.createdBy,
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
        self, params: OrderQueryParams
    ) -> ListResponse[OrderInDb]:
        raw_params = params.model_dump(exclude_unset=True)
        res = await self.orders_repo.get_paginated_orders(**raw_params)
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

    async def update_order_draft_by_id(
        self, order_id: str, body: UpdateOrder
    ) -> OrderInDb:
        updated_order = await self.orders_repo.update_order_draft_by_id(order_id, body)
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

        allowed_statuses = ["open", "draft"]

        if order.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not open",
            )

        cancelled_order = await cancel_order(order)

        return cancelled_order

    async def delete_order_draft_by_id(self, order_id: str) -> None:
        res = await self.orders_repo.delete_order_draft_by_id(order_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order is not found",
            )


orders_controller = OrdersController(
    orders_repo=OrdersRepository(
        orders_ds=OrdersDataSource(),
    ),
)
