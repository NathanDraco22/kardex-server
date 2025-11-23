from pydantic import BaseModel
from repos.v1.client_transactions.models.client_transaction_model import (
    TransactionType,
    TransactionSubType,
)


class ClientTransactionQueryParams(BaseModel):
    branchId: str | None = None
    clientId: str | None = None
    endDate: int | None = None
    type: TransactionType | None = None
    subtype: TransactionSubType | None = None
    offset: int = 0
    limit: int = 50

    def to_query(self):
        raw_query_dict = self.model_dump(exclude_none=True)

        if "endDate" in raw_query_dict:
            raw_query_dict["createdAt"] = {"$lte": raw_query_dict.pop("endDate")}

        return raw_query_dict
