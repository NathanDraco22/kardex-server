from typing import Any
from kardex.services.mongo_collections.v1 import DevolutionsCollection


class DevolutionsDataSource:
    async def create_devolution(self, devolution: dict[str, Any]) -> dict[str, Any]:
        collection = DevolutionsCollection.get_instance()
        await collection.create_devolution(devolution)
        return devolution

    async def get_all_devolutions(self, **kwargs) -> list[dict[str, Any]]:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_all_devolutions(**kwargs)

    async def get_all_active_devolutions(self, **kwargs) -> list[dict[str, Any]]:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_all_active_devolutions(**kwargs)

    async def get_devolutions_by_invoice_id(
        self, invoice_id: str, client_id: str | None
    ) -> list[dict[str, Any]]:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_devolutions_by_invoice_id(invoice_id, client_id)

    async def get_devolution_by_id(self, devolution_id: str) -> dict[str, Any] | None:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_devolution_by_id(devolution_id)

    async def get_devolution_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_devolution_by_doc_number(doc_number)

    async def update_devolution_by_id(
        self, devolution_id: str, devolution: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = DevolutionsCollection.get_instance()
        return await collection.update_devolution_by_id(devolution_id, devolution)

    async def delete_devolution_by_id(
        self, devolution_id: str
    ) -> dict[str, Any] | None:
        collection = DevolutionsCollection.get_instance()
        return await collection.delete_devolution_by_id(devolution_id)

    async def get_devolution_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = DevolutionsCollection.get_instance()
        return await collection.fetch_history_devolutions(**kwargs)
