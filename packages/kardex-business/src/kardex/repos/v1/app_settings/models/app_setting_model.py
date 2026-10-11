from pydantic import BaseModel


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


class AppSettingInDb(BaseAppSetting):
    id: str = "Default"
    createdAt: int
    updatedAt: int | None = None
