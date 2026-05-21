from typing import Any
from kardex.services.mongo_collections.v1 import SuppliersCollection


class SuppliersDataSource:
    async def create_supplier(self, supplier: dict[str, Any]) -> dict[str, Any]:
        collection = SuppliersCollection.get_instance()
        await collection.create_supplier(supplier)
        return supplier

    async def get_all_suppliers(self) -> list[dict[str, Any]]:
        collection = SuppliersCollection.get_instance()
        return await collection.fetch_all_suppliers()

    async def get_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = SuppliersCollection.get_instance()
        return await collection.fetch_supplier_by_id(supplier_id)

    async def search_supplier_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = SuppliersCollection.get_instance()
        return await collection.search_supplier_by_text(text_query)

    async def update_supplier_by_id(
        self, supplier_id: str, supplier: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = SuppliersCollection.get_instance()
        return await collection.update_supplier_by_id(supplier_id, supplier)
