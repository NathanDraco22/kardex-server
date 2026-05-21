from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection
from kardex.tools import TimeTools


class DevolutionsCollection(BaseMongoCollection):
    collection_name = "Devolutions"

    async def create_devolution(self, devolution: dict) -> None:
        collection = self._collection
        await collection.insert_one(devolution)

    async def fetch_all_devolutions(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}

        query = {key: value for key, value in kwargs.items() if value is not None}

        cursor = collection.find(query).sort("createdAt", -1)

        result = await cursor.to_list(length=None)

        return result

    async def fetch_all_active_devolutions(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}

        query = {key: value for key, value in kwargs.items() if value is not None}

        query["status"] = {"$in": ["confirmed", "open"]}

        cursor = collection.find(query).sort("createdAt", -1)

        result = await cursor.to_list(length=None)

        return result

    async def fetch_devolutions_by_invoice_id(
        self, invoice_id: str, client_id: str | None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query = {"originalInvoiceId": invoice_id}

        if client_id is not None:
            query["clientId"] = client_id

        cursor = collection.find(query)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_devolution_by_id(self, devolution_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": devolution_id})
        return result

    async def fetch_devolution_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def update_devolution_by_id(
        self,
        devolution_id: str,
        devolution: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": devolution_id},
            {"$set": devolution},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_devolution_by_id(
        self, devolution_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": devolution_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)]),
                IndexModel([("clientId", 1)]),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
            ]
        )

    async def create_devolution_with_session(
        self, devolution: dict, session: Any
    ) -> dict[str, Any]:
        collection = self._collection
        await collection.insert_one(devolution, session=session)

        return devolution

    async def update_devolution_status_by_id(
        self, devolution_id: str, status: str, session: Any
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": devolution_id},
            {
                "$set": {
                    "status": status,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def fetch_history_devolutions(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}

        query = {key: value for key, value in kwargs.items() if value is not None}

        if kwargs.get("endDate") is not None:
            query["createdAt"] = {
                "$lte": kwargs.get("endDate"),
            }
            del query["endDate"]

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)

        return result
