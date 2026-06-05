from typing import Any
from .base_filter_params import BaseFilterParams

class EntryHistoryFilterParams(BaseFilterParams):
    branchId: str
    supplierId: str | None = None
    startDate: int | None = None
    endDate: int | None = None

    def to_query_params(self) -> dict[str, Any]:
        return {
            "branch_id": self.branchId,
            "supplier_id": self.supplierId,
            "offset": self.offset,
            "limit": self.limit,
            "start_date": self.startDate,
            "end_date": self.endDate,
        }
