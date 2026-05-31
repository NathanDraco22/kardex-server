from pydantic import BaseModel
from typing import Any


class ExpensesFilterParams(BaseModel):
    offset: int
    limit: int = 50
    type: str | None = None
    status: str | None = None
    startDate: int | None = None
    endDate: int | None = None
    createdBy: str | None = None
    branchId: str | None = None
    category: str | None = None
    docNumber: str | None = None
    minAmount: int | None = None
    maxAmount: int | None = None

    def to_query_params(self) -> dict[str, Any]:
        raw_dict = self.model_dump(exclude_none=True)

        start_date = "startDate"
        end_date = "endDate"
        date_filter = {}

        if start_date in raw_dict:
            date_filter["$gte"] = raw_dict.pop(start_date)

        if end_date in raw_dict:
            date_filter["$lte"] = raw_dict.pop(end_date)

        if date_filter:
            raw_dict["createdAt"] = date_filter

        min_amount = "minAmount"
        max_amount = "maxAmount"
        amount_filter = {}

        if min_amount in raw_dict:
            amount_filter["$gte"] = raw_dict.pop(min_amount)

        if max_amount in raw_dict:
            amount_filter["$lte"] = raw_dict.pop(max_amount)

        if amount_filter:
            raw_dict["amount"] = amount_filter

        return raw_dict
