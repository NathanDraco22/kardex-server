from pydantic import BaseModel


class ReportQueryParams(BaseModel):
    startDate: int
    endDate: int
