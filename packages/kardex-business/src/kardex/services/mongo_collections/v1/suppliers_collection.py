import re
from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection

from pymongo import IndexModel


class SuppliersCollection(BaseMongoCollection):
    collection_name = "Suppliers"

    async def create_supplier(self, supplier: dict) -> None:
        collection = self._collection
        await collection.insert_one(supplier)

    async def create_many_suppliers_with_session(self, suppliers: list[dict], session: Any) -> None:
        collection = self._collection
        if suppliers:
            await collection.insert_many(suppliers, session=session)

    async def fetch_all_suppliers(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": supplier_id, "isDeleted": False})
        return result

    async def search_supplier_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self._collection

        safe_query = re.escape(text_query)

        query = {
            "name": {
                "$regex": safe_query,
                "$options": "i",  # 'i' para case-insensitive
            },
            "isDeleted": False,
        }

        cursor = collection.find(query).limit(7)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def update_supplier_by_id(
        self,
        supplier_id: str,
        supplier: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": supplier_id},
            {"$set": supplier},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def create_indexes(self):
        collection = self._collection
        text_index_name = "TextSearchIndex"
        desired_text_weights = {
            "name": 1,
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
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("name", "text"),
                    ],
                    weights=desired_text_weights,
                    name=text_index_name,
                ),
            ]
        )
