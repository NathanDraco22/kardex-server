from typing import Any
import re
from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class HoldSalesCollection(BaseMongoCollection):
    collection_name = "HoldSales"

    async def create_hold_sale(self, hold_sale: dict) -> None:
        collection = self._collection
        await collection.insert_one(hold_sale)

    async def fetch_all_hold_sales(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        offset = kwargs.pop("offset", 0)
        limit = kwargs.pop("limit", 50)
        branch_id = kwargs.pop("branchId", None)
        created_by = kwargs.pop("createdBy", None)
        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)
        search = kwargs.pop("search", None)

        query: dict[str, Any] = {}

        if branch_id:
            query["branchId"] = branch_id

        if created_by:
            query["createdBy.id"] = created_by

        if start_date is not None and end_date is not None:
            query["createdAt"] = {"$gte": start_date, "$lte": end_date}
        elif start_date is not None:
            query["createdAt"] = {"$gte": start_date}
        elif end_date is not None:
            query["createdAt"] = {"$lte": end_date}

        if search and search.strip():
            safe_search = re.escape(search.strip())
            query["$or"] = [
                {"description": {"$regex": safe_search, "$options": "i"}},
                {"client.name": {"$regex": safe_search, "$options": "i"}},
            ]

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_hold_sale_by_id(self, hold_sale_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": hold_sale_id})
        return result

    async def update_hold_sale_by_id(
        self,
        hold_sale_id: str,
        hold_sale: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": hold_sale_id},
            {"$set": hold_sale},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_hold_sale_by_id(self, hold_sale_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": hold_sale_id})
        return result

    async def delete_all_hold_sales_by_branch(self, branch_id: str) -> int:
        collection = self._collection
        res = await collection.delete_many({"branchId": branch_id})
        return res.deleted_count

