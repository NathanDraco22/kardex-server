from typing import Any
from .base_filter_params import BaseFilterParams
from kardex.repos.v1.client_transactions.models.client_transaction_model import (
    TransactionType,
    TransactionSubType,
)

class ClientTransactionFilterParams(BaseFilterParams):
    branchId: str | None = None
    clientId: str | None = None
    endDate: int | None = None
    startDate: int | None = None
    type: TransactionType | None = None
    subtype: TransactionSubType | None = None

    def to_query(self) -> dict[str, Any]:
        raw_query_dict = self.model_dump(exclude_none=True)
        raw_query_dict.pop("offset", None)
        raw_query_dict.pop("limit", None)

        if "endDate" in raw_query_dict:
            raw_query_dict["createdAt"] = {"$lte": raw_query_dict.pop("endDate")}

        if "startDate" in raw_query_dict and "endDate" not in raw_query_dict:
            raw_query_dict["createdAt"] = {"$gte": raw_query_dict.pop("startDate")}

        if "startDate" in raw_query_dict and "endDate" in raw_query_dict:
            raw_query_dict["createdAt"] = {
                "$gte": raw_query_dict.pop("startDate"),
                "$lte": raw_query_dict.pop("endDate"),
            }

        return raw_query_dict
