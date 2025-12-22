from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class ExecutiveSummariesCollection:
    collection_name = "ExecutiveSummaries"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_executive_summary(self, executive_summary: dict) -> None:
        collection = self.__collection
        await collection.insert_one(executive_summary)

    async def fetch_all_executive_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {}

        end_date = kwargs.get("endDate")
        start_date = kwargs.get("startDate")

        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)

        if end_date:
            query["$match"] = {
                "createdAt": {
                    "$lte": end_date,
                }
            }

        if end_date and start_date:
            query["$match"] = {
                "createdAt": {
                    "$gte": start_date,
                    "$lte": end_date,
                }
            }

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": executive_summary_id})
        return result

    async def update_executive_summary_by_id(
        self,
        executive_summary_id: str,
        executive_summary: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": executive_summary_id},
            {"$set": executive_summary},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": executive_summary_id})
        return result
