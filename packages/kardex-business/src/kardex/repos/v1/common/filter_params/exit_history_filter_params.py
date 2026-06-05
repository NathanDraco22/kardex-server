from typing import Any
from .base_filter_params import BaseFilterParams

class ExitHistoryFilterParams(BaseFilterParams):
    branchId: str
    clientId: str | None = None
    startDate: int | None = None
    endDate: int | None = None

    def to_query_params(self) -> dict[str, Any]:
        return {
            "branch_id": self.branchId,
            "client_id": self.clientId,
            "offset": self.offset,
            "limit": self.limit,
            "start_date": self.startDate,
            "end_date": self.endDate,
        }
