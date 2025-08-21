from typing import Any


def read_agreggation_exit_docs_with_client(
    branch_id: str,
    client_id: str | None,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    match_pipeline = {
        "$match": {
            "branchId": branch_id,
        },
    }

    if client_id:
        match_pipeline["$match"]["clientId"] = client_id

    return [
        match_pipeline,
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
