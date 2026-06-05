from pydantic import BaseModel

class ProductStatFilterParams(BaseModel):
    startDate: int
    endDate: int
    daysAnalysis: int

class ReadProductStatFilterParams(BaseModel):
    branchId: str | None = None
