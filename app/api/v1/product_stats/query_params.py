from pydantic import BaseModel


class ProductStatQueryParams(BaseModel):
    startDate: int
    endDate: int
    daysAnalysis: int


class ReadProductStatQueryParams(BaseModel):
    branchId: str | None = None
