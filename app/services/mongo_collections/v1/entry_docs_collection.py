from datetime import datetime
from typing import Any

from services import MongoService
from pymongo import IndexModel

from .aggregations.entry_docs_agregations import (
    read_agreggation_entry_docs_with_supplier,
)


class EntryDocsCollection:
    collection_name = "EntryDocs"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_entry_doc(self, entry_doc: dict) -> None:
        collection = self.__collection
        await collection.insert_one(entry_doc)

    async def fetch_all_entry_docs(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_paginated_entry_docs(
        self, offset: int, limit: int, branch_id: str
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find({"branchId": branch_id})
        cursor = cursor.sort("docDate", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)

        return result

    async def fetch_entry_doc_by_id(self, entry_doc_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": entry_doc_id})
        return result

    async def fetch_entry_doc_by_doc_number_and_supplier(
        self, supplier_id: str, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "supplierId": supplier_id,
                "docNumber": doc_number,
            },
        )
        return result

    async def fetch_entry_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {
                "docNumber": doc_number,
            },
        )
        return result

    async def create_entry_doc_with_session(self, entry_doc_data: dict, session: Any):
        collection = self.__collection
        await collection.insert_one(entry_doc_data, session=session)
        return entry_doc_data

    async def create_index(self):
        collection = self.__collection

        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("docNumber", 1),
                        ("supplierId", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("docDate", -1),
                    ],
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("supplierId", 1),
                        ("docDate", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("createdAt", -1),
                    ],
                ),
            ]
        )

    async def fetch_entry_docs_with_supplier(
        self,
        branch_id: str,
        supplier_id: str | None,
        offset: int,
        limit: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        collection = self.__collection

        pipeline = read_agreggation_entry_docs_with_supplier(
            branch_id,
            supplier_id,
            offset,
            limit,
            start_date,
            end_date,
        )

        cursor = collection.aggregate(pipeline)

        return await cursor.to_list(length=None)
