from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class UnitsCollection(BaseMongoCollection):
    collection_name = "Units"

    async def create_unit(self, unit: dict) -> None:
        collection = self._collection
        await collection.insert_one(unit)

    async def fetch_all_units(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": unit_id})
        return result

    async def update_unit_by_id(
        self,
        unit_id: str,
        unit: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": unit_id},
            {"$set": unit},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": unit_id})
        return result
