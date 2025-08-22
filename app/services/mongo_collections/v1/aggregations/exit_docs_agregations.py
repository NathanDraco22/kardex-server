from typing import Any
from datetime import datetime


def read_agreggation_exit_docs_with_client(
    branch_id: str,
    client_id: str | None,
    offset: int,
    limit: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    match_pipeline: dict[str, Any] = {
        "branchId": branch_id,
    }

    if client_id:
        match_pipeline["clientId"] = client_id

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
                "from": "Clients",
                "localField": "clientId",
                "foreignField": "id",
                "as": "client",
            }
        },
        {
            "$unwind": "$client",
        },
    ]
