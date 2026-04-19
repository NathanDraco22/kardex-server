from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class AdjustEntriesCollection:
    collection_name = "AdjustEntries"
    _instance: "AdjustEntriesCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_adjust_entry(self, adjust_entry: dict) -> None:
        collection = self.__collection
        await collection.insert_one(adjust_entry)

    async def create_adjust_entry_with_session(
        self, adjust_entry: dict, session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_one(adjust_entry, session=session)

    async def fetch_all_adjust_entries(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        offset = kwargs.pop("offset", 0)
        limit = kwargs.pop("limit", 50)

        end_date = kwargs.pop("endDate", None)

        query = kwargs

        if end_date:
            query["createdAt"] = {"$lte": end_date}

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": adjust_entry_id})
        return result

    async def fetch_adjust_entry_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "docNumber": doc_number,
                "branchId": branch_id,
            }
        )
        return result

    async def update_adjust_entry_by_id(
        self,
        adjust_entry_id: str,
        adjust_entry: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": adjust_entry_id},
            {"$set": adjust_entry},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_adjust_entry_by_id(
        self, adjust_entry_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": adjust_entry_id})
        return result

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel(
                    [("docNumber", 1), ("branchId", 1)],
                    unique=True,
                ),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("createdAt", -1)]),
            ]
        )
