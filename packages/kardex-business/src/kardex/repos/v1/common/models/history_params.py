from pydantic import BaseModel


class HistoryParams(BaseModel):
    offset: int
    limit: int = 50
    startDate: int | None = None
    endDate: int | None = None
    createdBy: str | None = None


class HistoryBranchParams(HistoryParams):
    branchId: str | None = None


class HistoryClientParams(HistoryParams):
    clientId: str | None = None
    branchId: str | None = None

    def to_query_params(self) -> dict[str, str]:
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

        if "createdBy" in raw_dict:
            raw_dict["createdBy.id"] = raw_dict.pop("createdBy")

        return raw_dict
