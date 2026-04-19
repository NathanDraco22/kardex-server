from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class DailySummariesCollection:
    collection_name = "DailySummaries"
    _instance: "DailySummariesCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_daily_summary(self, daily_summary: dict) -> None:
        collection = self.__collection
        await collection.insert_one(daily_summary)

    async def fetch_all_daily_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {}

        end_date = kwargs.get("endDate")
        start_date = kwargs.get("startDate")

        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)

        if end_date and start_date:
            query["createdAt"] = {"$gte": start_date, "$lte": end_date}
        elif end_date:
            query["createdAt"] = {"$lte": end_date}

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_daily_summary_by_start_date_range(self, **kwargs):
        collection = self.__collection

        query = {}

        end_date = kwargs.get("endDate")
        start_date = kwargs.get("startDate")

        if end_date and start_date:
            query["startDate"] = {"$gte": start_date, "$lte": end_date}
        elif end_date:
            query["startDate"] = {"$lte": end_date}

        cursor = collection.find(query).sort("startDate", -1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": daily_summary_id})
        return result

    async def fetch_daily_summary_by_date_id(
        self, date_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "dateId": {
                    "$regex": f"^{date_id}",
                },
            },
        )
        return result

    async def update_daily_summary_by_id(
        self,
        daily_summary_id: str,
        daily_summary: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": daily_summary_id},
            {"$set": daily_summary},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": daily_summary_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("dateId", 1)], unique=True),
                IndexModel([("branches.branchId", 1)]),
                IndexModel([("createdAt", -1)]),
                IndexModel([("startDate", -1)]),
            ]
        )
