from typing import Any

from services import MongoService

from pymongo import IndexModel

from .aggregations.exit_docs_agregations import (
    read_agreggation_exit_docs_with_client,
)


class ExitDocsCollection:
    collection_name = "ExitDocs"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_exit_doc(self, exit_doc: dict) -> None:
        collection = self.__collection
        await collection.insert_one(exit_doc)

    async def fetch_all_exit_docs(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_paginated_exit_docs(
        self, offset: int, limit: int, branch_id: str
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"branchId": branch_id})
        cursor = cursor.sort("docDate", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_exit_doc_by_id(self, exit_doc_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": exit_doc_id})
        return result

    async def fetch_exit_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def fetch_exit_doc_by_doc_number_and_branch(
        self,
        doc_number: str,
        branch_id: str,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "docNumber": doc_number,
                        "branchId": branch_id,
                    }
                },
                {
                    "$lookup": {
                        "from": "Clients",
                        "localField": "clientId",
                        "foreignField": "id",
                        "as": "client",
                    }
                },
                {"$unwind": "$client"},
            ]
        )

        result = await cursor.to_list(length=None)

        if result:
            return result[0]

        return None

    async def fetch_exit_doc_by_doc_number_and_client(
        self,
        client_id: str,
        doc_number: str,
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "docNumber": doc_number,
                "clientId": client_id,
            }
        )
        return result

    async def create_exit_doc_with_session(self, exit_doc: dict, session: Any) -> dict:
        collection = self.__collection
        await collection.insert_one(
            exit_doc,
            session=session,
        )

        return exit_doc

    async def create_index(self):
        collection = self.__collection

        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("docNumber", 1),
                        ("branchId", 1),
                    ],
                ),
                IndexModel(
                    [
                        ("docNumber", 1),
                        ("clientId", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("docDate", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("clientId", 1),
                        ("docDate", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("createdAt", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("docDate", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("createdBy.id", 1),
                    ],
                ),
            ]
        )

    async def fetch_exit_docs_with_client(
        self,
        branch_id: str,
        client_id: str | None,
        offset: int,
        limit: int,
        start_date: int | None = None,
        end_date: int | None = None,
    ) -> list[dict[str, Any]]:
        collection = self.__collection

        pipeline = read_agreggation_exit_docs_with_client(
            branch_id,
            client_id,
            offset,
            limit,
            start_date,
            end_date,
        )

        cursor = collection.aggregate(pipeline)

        return await cursor.to_list(length=None)
