from typing import Any


def read_agreggation_entry_docs_with_supplier(
    branch_id: str,
    supplier_id: str | None,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    match_pipeline = {
        "$match": {
            "branchId": branch_id,
        },
    }

    if supplier_id:
        match_pipeline["$match"]["supplierId"] = supplier_id

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
