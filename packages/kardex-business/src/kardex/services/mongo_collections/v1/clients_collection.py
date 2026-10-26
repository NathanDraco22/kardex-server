import re
from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection
from kardex.tools import MongoMigrationException

from pymongo import IndexModel


class ClientsCollection(BaseMongoCollection):
    collection_name = "Clients"

    async def create_client(self, client: dict) -> None:
        collection = self._collection
        await collection.insert_one(client)

    async def create_client_with_session(self, client: dict, session: Any) -> None:
        collection = self._collection
        await collection.insert_one(client, session=session)

    async def create_many_clients_with_session(
        self, clients: list[dict], session: Any
    ) -> None:
        collection = self._collection
        if clients:
            await collection.insert_many(clients, session=session)

    async def create_client_if_absent(self, client_id: str, client: dict) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": client_id},
            {"$setOnInsert": client},
            upsert=True,
        )

    async def fetch_all_clients(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        group_param = kwargs.pop("group", None)
        hasMovements = kwargs.pop("hasMovements", None)

        query = {}
        if group_param:
            query = {"group": group_param}

        if hasMovements is not None:
            query = {"hasMovements": hasMovements}

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
        collection = self._collection
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
        collection = self._collection

        safe_query = re.escape(text_query)

        pipeline = [
            {
                "$match": {
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
            },
            {
                "$addFields": {
                    "baseScore": {"$meta": "textScore"},
                    "positionBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$name",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                }
            },
            {"$addFields": {"finalScore": {"$add": ["$baseScore", "$positionBoost"]}}},
            {"$sort": {"finalScore": -1, "name": 1}},
            {"$limit": 20},
            {"$project": {"baseScore": 0, "positionBoost": 0, "finalScore": 0}},
        ]
        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": client_id, "isDeleted": False})
        return result

    async def get_client_by_card_id(self, card_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"cardId": card_id, "isDeleted": False})
        return result

    async def search_client_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self._collection

        safe_query = re.escape(text_query)

        pipeline = [
            {
                "$match": {
                    "$text": {
                        "$search": safe_query,
                        "$caseSensitive": False,
                        "$diacriticSensitive": False,
                    },
                    "isDeleted": False,
                    "isInternal": False,
                }
            },
            {
                "$addFields": {
                    "baseScore": {"$meta": "textScore"},
                    "positionBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$name",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                }
            },
            {"$addFields": {"finalScore": {"$add": ["$baseScore", "$positionBoost"]}}},
            {"$sort": {"finalScore": -1, "name": 1}},
            {"$limit": 20},
            {"$project": {"baseScore": 0, "positionBoost": 0, "finalScore": 0}},
        ]
        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def update_client_by_id(
        self,
        client_id: str,
        client: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

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
        collection = self._collection
        await collection.update_many(
            {"group": old_group}, {"$set": {"group": new_group}}
        )

    async def create_indexes(self):
        collection = self._collection
        text_index_name = "TextSearchIndex"
        desired_text_weights = {
            "name": 10,
            "searchPrefixes": 5,
            "group": 1,
            "cardId": 1,
            "phone": 1,
            "id": 1,
        }

        # Inspeccionar índices existentes para eliminar cualquier índice de texto previo
        # que sea autogenerado o que difiera del nombre/pesos actuales.
        existing_indexes = await collection.index_information()
        for idx_name, idx_info in existing_indexes.items():
            is_text_index = "weights" in idx_info or any(
                k[1] == "text" for k in idx_info.get("key", [])
            )
            if is_text_index:
                current_weights = idx_info.get("weights", {})
                if idx_name != text_index_name or current_weights != desired_text_weights:
                    await collection.drop_index(idx_name)

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
                        ("group", "text"),
                        ("cardId", "text"),
                        ("phone", "text"),
                        ("id", "text"),
                    ],
                    weights=desired_text_weights,
                    name=text_index_name,
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
        collection = self._collection
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

        if result is None:
            raise MongoMigrationException("Failed to add to client balance: result is None")

        return result

    async def substract_from_client_balance(
        self, client_id: str, amount: int, session: Any, timestamp: int
    ) -> dict[str, Any]:
        collection = self._collection
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

        if result is None:
            raise MongoMigrationException("Failed to substract from client balance: result is None")

        return result
