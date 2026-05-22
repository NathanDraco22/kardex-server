from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class TransfersCollection(BaseMongoCollection):
    collection_name = "Transfers"

    async def create_transfer(self, transfer: dict) -> None:
        collection = self._collection
        await collection.insert_one(transfer)

    async def create_transfer_with_session(self, transfer: dict, session) -> None:
        collection = self._collection
        await collection.insert_one(transfer, session=session)

    async def fetch_all_transfers(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        raw_params = kwargs

        query = {}

        offset = raw_params.pop("offset", 0)
        limit = raw_params.pop("limit", 50)

        query = raw_params

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_transfer_by_id(self, transfer_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": transfer_id})
        return result

    async def fetch_tranfer_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def fetch_transfer_by_id_with_session(
        self, transfer_id: str, session
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": transfer_id}, session=session)
        return result

    async def update_transfer_by_id(
        self,
        transfer_id: str,
        transfer: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": transfer_id},
            {"$set": transfer},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_transfer_status_with_session(
        self, transfer_id: str, update_data: dict, session
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": transfer_id},
            {"$set": update_data},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_transfer_by_id(self, transfer_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": transfer_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True, name="unique_id_index"),
                IndexModel(
                    [("docNumber", 1)], unique=True, name="unique_docNumber_index"
                ),
                IndexModel(
                    [
                        ("origin", 1),  # Filtro (Equality)
                        ("createdAt", -1),  # Orden (Sort)
                    ],
                    name="origin_date_index",
                ),
                IndexModel(
                    [
                        ("destination", 1),  # Filtro (Equality)
                        ("createdAt", -1),  # Orden (Sort)
                    ],
                    name="destination_date_index",
                ),
                IndexModel([("createdAt", -1)], name="global_date_index"),
            ]
        )
