from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService

from tools import TimeTools


class OrdersCollection:
    collection_name = "Orders"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_order(self, order: dict) -> None:
        collection = self.__collection
        await collection.insert_one(order)

    async def create_order_with_session(self, order: dict, session: Any) -> dict:
        collection = self.__collection
        await collection.insert_one(order, session=session)
        return order

    async def fetch_paginated_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        skip = kwargs.pop("skip", 0)
        limit = kwargs.pop("limit", 50)
        status = kwargs.pop("status", None)
        cliend_id = kwargs.pop("clientId", None)
        branch_id = kwargs.pop("branchId", None)

        query = {}

        if branch_id:
            query["branchId"] = branch_id

        if cliend_id:
            query["clientId"] = cliend_id

        if status:
            query["status"] = status

        cursor = collection.find(query).sort("createdAt", -1).skip(skip).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": order_id})
        return result

    async def fetch_order_by_doc_number(self, doc_number: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def update_order_draft_by_id(
        self,
        order_id: str,
        order: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {
                "id": order_id,
                "status": "draft",
            },
            {"$set": order},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_order_by_doc_number(
        self,
        doc_number: str,
        order: dict,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"docNumber": doc_number},
            {"$set": order},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def update_order_status_by_doc_number(
        self,
        doc_number: str,
        status: str,
        session: Any,
    ) -> None:
        collection = self.__collection

        await collection.update_one(
            {"docNumber": doc_number},
            {
                "$set": {
                    "status": status,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
        )

    async def delete_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": order_id})
        return result

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self.__collection
        return await collection.find_one_and_update(
            {"id": order_id},
            {
                "$set": {
                    "status": status,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)]),
                IndexModel([("clientId", 1), ("status", 1), ("createdAt", -1)]),
                IndexModel(
                    [("branchId", 1), ("clientId", 1), ("status", 1), ("createdAt", -1)]
                ),
                IndexModel([("status", 1), ("createdAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("invoiceId", 1)]),
            ]
        )
