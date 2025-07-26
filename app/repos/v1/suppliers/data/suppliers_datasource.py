from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import SuppliersCollection


class SuppliersDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_supplier(self, supplier: dict[str, Any]) -> dict[str, Any]:
        collection = SuppliersCollection()
        await collection.create_supplier(supplier)
        return supplier

    async def get_all_suppliers(self) -> list[dict[str, Any]]:
        collection = SuppliersCollection()
        return await collection.fetch_all_suppliers()

    async def get_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = SuppliersCollection()
        return await collection.fetch_supplier_by_id(supplier_id)

    async def update_supplier_by_id(
        self, supplier_id: str, supplier: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = SuppliersCollection()
        return await collection.update_supplier_by_id(supplier_id, supplier)

    async def delete_supplier_by_id(self, supplier_id: str) -> dict[str, Any] | None:
        collection = SuppliersCollection()
        return await collection.delete_supplier_by_id(supplier_id)
