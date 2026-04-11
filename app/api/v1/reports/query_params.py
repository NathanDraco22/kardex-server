from pydantic import BaseModel


class ReportQueryParams(BaseModel):
    startDate: int
    endDate: int


class TotalsQueryParams(BaseModel):
    branchId: str
    startDate: int
    endDate: int
