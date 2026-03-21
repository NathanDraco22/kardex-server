import re
from typing import Any

from pymongo import ReturnDocument
from services import MongoService

from pymongo import IndexModel


class ClientsCollection:
    collection_name = "Clients"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_client(self, client: dict) -> None:
        collection = self.__collection
        await collection.insert_one(client)

    async def create_client_with_session(self, client: dict, session: Any) -> None:
        collection = self.__collection
        await collection.insert_one(client, session=session)

    async def create_client_if_absent(self, client_id: str, client: dict) -> None:
        collection = self.__collection
        await collection.update_one(
            {"id": client_id},
            {"$setOnInsert": client},
            upsert=True,
        )

    async def fetch_all_clients(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection
        group_param = kwargs.pop("group", None)

        query = {}
        if group_param:
            query = {"group": group_param}

        cursor = collection.find(
            {
                "isDeleted": False,
                "isInternal": False,
                **query,
            }
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_clients_with_balance(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection
        group_param = kwargs.pop("group", None)

        query = {}
        if group_param:
            query = {"group": group_param}

        query = {
            "isDeleted": False,
            "isInternal": False,
            **query,
            "balance": {
                "$ne": 0,
            },
        }

        filtered_params = {
            key: value for key, value in kwargs.items() if value is not None
        }

        offset = filtered_params.pop("offset", 0)
        limit = filtered_params.pop("limit", 50)

        if filtered_params:
            query.update(filtered_params)

        cursor = collection.find(query).skip(offset).limit(limit)

        cursor.sort("name", 1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def search_clients_with_balance(
        self,
        text_query: str,
    ) -> list[dict[str, Any]]:
        collection = self.__collection

        safe_query = re.escape(text_query)

        query = {
            "$text": {
                "$search": safe_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            },
            "isDeleted": False,
            "isInternal": False,
            "balance": {
                "$ne": 0,
            },
        }
        cursor = collection.find(query).sort("name", 1).limit(10)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": client_id, "isDeleted": False})
        return result

    async def get_client_by_card_id(self, card_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"cardId": card_id, "isDeleted": False})
        return result

    async def search_client_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self.__collection

        safe_query = re.escape(text_query)

        query = {
            "$text": {
                "$search": safe_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            },
            "isDeleted": False,
            "isInternal": False,
        }

        cursor = collection.find(query).limit(7)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def update_client_by_id(
        self,
        client_id: str,
        client: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": client_id},
            {"$set": client},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_group(
        self,
        old_group: str,
        new_group: str,
    ):
        collection = self.__collection
        await collection.update_many(
            {"group": old_group}, {"$set": {"group": new_group}}
        )

    async def create_indexes(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                        ("isDeleted", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("group", 1),
                    ],
                ),
                IndexModel(
                    [
                        ("name", "text"),
                        ("searchPrefixes", "text"),
                        ("location", "text"),
                        ("group", "text"),
                        ("cardId", "text"),
                        ("phone", "text"),
                        ("id", "text"),
                    ],
                ),
                IndexModel(
                    [
                        ("cardId", 1),
                    ],
                ),
            ]
        )

    async def add_to_client_balance(
        self, client_id: str, amount: int, timestamp: int, session: Any
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = timestamp

        result = await collection.find_one_and_update(
            {"id": client_id},
            [
                {
                    "$set": {
                        "lastCreditStart": {
                            "$cond": {
                                "if": {"$lte": ["$balance", 0]},
                                "then": updated_at,
                                "else": "$lastCreditStart",
                            }
                        }
                    }
                },
                {
                    "$set": {
                        "lastReceiptDate": {
                            "$cond": {
                                "if": {"$lte": ["$balance", 0]},
                                "then": None,
                                "else": "$lastReceiptDate",
                            }
                        }
                    }
                },
                {
                    "$set": {
                        "balance": {"$add": [{"$ifNull": ["$balance", 0]}, amount]},
                        "updatedAt": updated_at,
                        "hasMovements": True,
                    },
                },
            ],
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def substract_from_client_balance(
        self, client_id: str, amount: int, session: Any, timestamp: int
    ) -> dict[str, Any]:
        collection = self.__collection
        updated_at = timestamp

        result = await collection.find_one_and_update(
            {"id": client_id},
            {
                "$inc": {
                    "balance": -abs(amount),
                },
                "$set": {
                    "updatedAt": updated_at,
                    "lastReceiptDate": updated_at,
                    "hasMovements": True,
                },
            },
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result
