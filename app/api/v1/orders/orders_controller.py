from fastapi import HTTPException, status
from kardex.repos.v1.invoices.models.invoice_model import (
    InvoiceInDb,
    CreateInvoice,
    InvoiceStatus,
    OrderInfo,
)
from kardex.repos.v1.common.models.invoice_product_sale import ProductSalesTotal
from kardex.core.inventory import calculate_line_amount
from kardex.core.order_register.order_register import OrderRegister
from kardex.core.invoice_register.invoice_register import InvoiceRegister
from kardex.core.order_register.cancel_order import cancel_order
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.orders import (
    CreateOrder,
    UpdateOrder,
    OrderInDb,
    OrdersRepository,
    OrdersDataSource,
)

from responses.v1 import ListResponse
from kardex.repos.v1.common.filter_params import OrderFilterParams
from kardex.repos.v1.common.models import (
    PaymentDetail,
    PaymentType,
    ProductStockDemand,
    UserInfo,
)
from kardex.repos.v1.users import UsersRepository, UsersDataSource
from kardex.tools.app_settings_tool import AppSettingsTool


class OrdersController:
    def __init__(
        self,
        orders_repo: OrdersRepository,
        users_repo: UsersRepository | None = None,
        app_settings_tool: AppSettingsTool | None = None,
    ) -> None:
        self.orders_repo = orders_repo
        self.users_repo = users_repo or UsersRepository(UsersDataSource())
        self.app_settings_tool = app_settings_tool or AppSettingsTool()
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
        self,
        order_id: str,
        invoiced_by_user_id: str | None = None,
        invoiced_by_username: str | None = None,
        shift_id: str | None = None,
        payment_type: PaymentType | None = None,
        bank_reference: str | None = None,
        payment_detail: PaymentDetail | None = None,
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

        # Recalcular totalCost desde los items con costos actualizados
        # (process_invoice reasignará los costs con el costo real del inventario)
        order_total_cost = sum(
            calculate_line_amount(
                item.cost,
                item.quantity + item.bonQuantity,
                item.priceUnitFactor,
            )
            for item in order.saleItems
        )

        invoiced_by: UserInfo | None = None
        if invoiced_by_user_id:
            auth_user = await self.users_repo.get_user_by_id(invoiced_by_user_id)
            resolved_name = (
                (auth_user.username if auth_user is not None else "")
                or (invoiced_by_username or "")
            )
            if resolved_name.strip():
                invoiced_by = UserInfo(
                    id=invoiced_by_user_id,
                    name=resolved_name.strip(),
                )

        settings = await self.app_settings_tool.get_current_app_settings()
        should_charge_to_shift = bool(
            settings and settings.useShifts and settings.chargeConvertedOrdersToShift
        )
        target_shift_id: str | None = (
            ((shift_id or "").strip() or None) if should_charge_to_shift else None
        )

        effective_payment_type: PaymentType = payment_type or order.paymentType
        effective_bank_reference = (
            (bank_reference or "").strip()
            if effective_payment_type != "credit"
            else ""
        )
        effective_payment_detail = (
            payment_detail if effective_payment_type != "credit" else None
        )

        create_invoice = CreateInvoice(
            branchId=order.branchId,
            clientId=order.clientId,
            clientInfo=order.clientInfo,
            orderNumber=order.docNumber,
            orderInfo=OrderInfo(
                id=order.id,
                docNumber=order.docNumber,
                createdAt=order.createdAt,
                createdBy=order.createdBy,
            ),
            saleItems=order.saleItems,
            description=order.description,
            amountPaid=order.amountPaid,
            totalCost=order_total_cost,
            paymentType=effective_payment_type,
            bankReference=effective_bank_reference,
            paymentDetail=effective_payment_detail,
            status=new_invoice_status,
            total=order.total,
            createdBy=order.createdBy,
            invoicedBy=invoiced_by,
            shiftId=target_shift_id,
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
        self, params: OrderFilterParams
    ) -> ListResponse[OrderInDb]:
        res = await self.orders_repo.get_paginated_orders(params)
        return ListResponse(
            count=len(res),
            data=res,
        )

    async def get_product_in_orders(
        self, params: OrderFilterParams
    ) -> ListResponse[ProductSalesTotal]:
        res = await self.orders_repo.get_products_in_orders(params)
        return ListResponse(count=len(res), data=res)

    async def get_product_demand_vs_inventory(
        self, params: OrderFilterParams
    ) -> ListResponse[ProductStockDemand]:
        res = await self.orders_repo.get_demand_vs_stock(params)
        return ListResponse(count=len(res), data=res)

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

    async def delete_order_draft_by_id(self, order_id: str) -> OrderInDb:
        res = await self.orders_repo.delete_order_draft_by_id(order_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order is not found",
            )
        return res


orders_controller = OrdersController(
    orders_repo=OrdersRepository(
        orders_ds=OrdersDataSource(),
    ),
)
