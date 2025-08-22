from datetime import datetime
from typing import Any


def read_agreggation_entry_docs_with_supplier(
    branch_id: str,
    supplier_id: str | None,
    offset: int,
    limit: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    match_pipeline: dict[str, Any] = {
        "branchId": branch_id,
    }

    if supplier_id:
        match_pipeline["supplierId"] = supplier_id

    if start_date and end_date:
        match_pipeline["docDate"] = {
            "$gte": start_date,
            "$lte": end_date,
        }

    return [
        {
            "$match": match_pipeline,
        },
        {
            "$sort": {
                "docDate": -1,
            }
        },
        {
            "$skip": offset,
        },
        {
            "$limit": limit,
        },
        {
            "$lookup": {
                "from": "Suppliers",
                "localField": "supplierId",
                "foreignField": "id",
                "as": "supplier",
            }
        },
        {
            "$unwind": "$supplier",
        },
    ]
