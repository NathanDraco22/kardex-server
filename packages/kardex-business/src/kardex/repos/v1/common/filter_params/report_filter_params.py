from pydantic import BaseModel

class ReportFilterParams(BaseModel):
    startDate: int
    endDate: int

class TotalsFilterParams(BaseModel):
    branchId: str
    startDate: int
    endDate: int
