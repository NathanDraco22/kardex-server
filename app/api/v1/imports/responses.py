from pydantic import BaseModel


class ImportResponse(BaseModel):
    status: str
    message: str
    importedCount: int


class ImportPreviewError(BaseModel):
    row: int
    field: str | None = None
    message: str


class ImportPreviewResponse(BaseModel):
    status: str = "success"
    isValid: bool
    importType: str
    totalRows: int
    totalQuantity: int = 0
    totalCost: int = 0
    totalPrice: int = 0
    totalCreditLimit: int = 0
    totalInitialBalance: int = 0
    errors: list[ImportPreviewError] = []
