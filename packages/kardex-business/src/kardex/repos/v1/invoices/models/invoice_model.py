from typing import Literal

from pydantic import BaseModel

from kardex.repos.v1.common.models import (
    SaleItem,
    PaymentType,
    DiscountType,
    ClientInfo,
    UserInfo,
    OrderInfo,
    PaymentDetail,
)

InvoiceStatus = Literal["draft", "open", "paid", "partiallyPaid", "cancelled"]


class BaseInvoice(BaseModel):
    branchId: str
    clientId: str
    clientInfo: ClientInfo
    docNumber: str = ""
    orderNumber: str = ""
    orderInfo: OrderInfo | None = None
    saleItems: list[SaleItem]
    description: str = ""
    amountPaid: int = 0
    status: InvoiceStatus
    paymentType: PaymentType
    bankReference: str = ""
    paymentDetail: PaymentDetail | None = None
    discountType: DiscountType | None = None
    discountValue: int = 0
    itemDiscounts: int = 0
    invoiceDiscount: int = 0
    totalCost: int
    total: int
    paidAt: int | None = None
    createdBy: UserInfo
    invoicedBy: UserInfo | None = None
    shiftId: str | None = None
    cancelledAt: int | None = None
    cancelledBy: UserInfo | None = None
    cancellationReason: str | None = None
    cancellationRequestId: str | None = None

    @property
    def itemsSubTotal(self) -> int:
        return sum(item.subTotal for item in self.saleItems)

    @property
    def effectiveItemDiscounts(self) -> int:
        return (
            self.itemDiscounts
            if self.itemDiscounts > 0
            else sum(item.totalDiscount for item in self.saleItems)
        )

    @property
    def totalDiscount(self) -> int:
        return self.effectiveItemDiscounts + self.invoiceDiscount

    @property
    def totalRemaining(self) -> int:
        return max(0, self.total - self.amountPaid)


class CreateInvoice(BaseInvoice):
    pass


class UpdateInvoice(BaseModel):
    amountPaid: int | None = None
    status: InvoiceStatus | None = None
    pass


class InvoiceInDb(BaseInvoice):
    id: str
    createdAt: int
    updatedAt: int | None = None
