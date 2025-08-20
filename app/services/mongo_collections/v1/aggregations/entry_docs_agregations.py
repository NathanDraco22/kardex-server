from typing import Any


def read_agreggation_entry_docs_with_supplier(
    branch_id: str,
    supplier_id: str,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    return [
        {
            "$match": {
                "branchId": branch_id,
                "supplierId": supplier_id,
            },
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
