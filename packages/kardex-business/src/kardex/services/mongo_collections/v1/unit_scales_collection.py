from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class UnitScalesCollection(BaseMongoCollection):
    collection_name = "UnitScales"

    async def create_unit_scale(self, unit_scale: dict) -> None:
        collection = self._collection
        await collection.insert_one(unit_scale)

    async def create_unit_scale_if_absent(self, name: str, unit_scale: dict) -> None:
        collection = self._collection
        await collection.update_one(
            {"name": name},
            {"$setOnInsert": unit_scale},
            upsert=True,
        )

    async def fetch_all_unit_scales(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find().sort("name", 1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_unit_scale_by_id(self, unit_scale_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": unit_scale_id})
        return result

    async def update_unit_scale_by_id(
        self,
        unit_scale_id: str,
        unit_scale: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": unit_scale_id},
            {"$set": unit_scale},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_unit_scale_by_id(self, unit_scale_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": unit_scale_id})
        return result
