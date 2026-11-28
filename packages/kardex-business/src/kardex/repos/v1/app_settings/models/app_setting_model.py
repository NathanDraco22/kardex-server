from typing import Literal

from pydantic import BaseModel, Field

CurrencyCode = Literal["NIO", "USD", "HNL", "GTQ", "CRC", "COP", "MXN", "EUR"]


class BaseAppSetting(BaseModel):
    useDefaultProfitMargin: bool = False
    defaultProfitMargin: float = 20.0
    useExpirationDates: bool = True
    useOrders: bool = True
    useQuotations: bool = True
    allowNegativeStock: bool = False
    alertMinStock: bool = True
    defaultPaymentTermDays: int = 30
    useHoldSales: bool = True
    useQuickProductSearch: bool = False
    currency: CurrencyCode = "NIO"
    secondaryCurrency: CurrencyCode = "USD"
    exchangeRate: float = Field(default=0.0, ge=0)
    showInvoiceTotalInSecondaryCurrency: bool = False
    allowSecondaryCurrencyPayment: bool = False
    useAbonoReceivedAmount: bool = False
    showInvoiceItemsSummary: bool = False
    showInvoiceOrderCreator: bool = False
    companyLogoUrl: str | None = None
    useShifts: bool = False
    chargeConvertedOrdersToShift: bool = False
    requireShiftForConvertedOrders: bool = False
    useInvoiceCancellations: bool = False
    useReceiptCancellations: bool = False
    allowCancellationsOutsideShift: bool = False
    useDiscounts: bool = False
    roundUpInvoiceTotals: bool = False
    taxIdLabel: str = Field(default="RUC", min_length=1, max_length=32)


class CreateAppSetting(BaseAppSetting):
    id: str = "Default"


class UpdateAppSetting(BaseModel):
    useDefaultProfitMargin: bool | None = None
    defaultProfitMargin: float | None = None
    useExpirationDates: bool | None = None
    useOrders: bool | None = None
    useQuotations: bool | None = None
    allowNegativeStock: bool | None = None
    alertMinStock: bool | None = None
    defaultPaymentTermDays: int | None = None
    useHoldSales: bool | None = None
    useQuickProductSearch: bool | None = None
    currency: CurrencyCode | None = None
    secondaryCurrency: CurrencyCode | None = None
    exchangeRate: float | None = Field(default=None, ge=0)
    showInvoiceTotalInSecondaryCurrency: bool | None = None
    allowSecondaryCurrencyPayment: bool | None = None
    useAbonoReceivedAmount: bool | None = None
    showInvoiceItemsSummary: bool | None = None
    showInvoiceOrderCreator: bool | None = None
    companyLogoUrl: str | None = None
    useShifts: bool | None = None
    chargeConvertedOrdersToShift: bool | None = None
    requireShiftForConvertedOrders: bool | None = None
    useInvoiceCancellations: bool | None = None
    useReceiptCancellations: bool | None = None
    allowCancellationsOutsideShift: bool | None = None
    useDiscounts: bool | None = None
    roundUpInvoiceTotals: bool | None = None
    taxIdLabel: str | None = Field(default=None, min_length=1, max_length=32)


class AppSettingInDb(BaseAppSetting):
    id: str = "Default"
    createdAt: int
    updatedAt: int | None = None
