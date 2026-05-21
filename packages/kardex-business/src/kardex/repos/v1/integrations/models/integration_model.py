from pydantic import BaseModel


class TelegramIntegration(BaseModel):
    isActive: bool = False
    reportId: str = ""
    adjustmentId: str = ""


class BaseIntegration(BaseModel):
    telegram: TelegramIntegration = TelegramIntegration()


class CreateIntegration(BaseIntegration):
    pass


class UpdateIntegration(BaseModel):
    telegram: TelegramIntegration | None = None
    pass


class IntegrationInDb(BaseIntegration):
    id: str = "Default"
    createdAt: int
    updatedAt: int | None = None
