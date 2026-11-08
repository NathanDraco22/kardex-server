from typing import Any
from kardex.services.mongo_collections.v1 import UnitScalesCollection


class UnitScalesDataSource:

    async def create_unit_scale(self, unit_scale: dict[str, Any]) -> dict[str, Any]:
        collection = UnitScalesCollection.get_instance()
        await collection.create_unit_scale(unit_scale)
        return unit_scale

    async def get_all_unit_scales(self) -> list[dict[str, Any]]:
        collection = UnitScalesCollection.get_instance()
        return await collection.fetch_all_unit_scales()

    async def get_unit_scale_by_id(self, unit_scale_id: str) -> dict[str, Any] | None:
        collection = UnitScalesCollection.get_instance()
        return await collection.fetch_unit_scale_by_id(unit_scale_id)

    async def update_unit_scale_by_id(
        self, unit_scale_id: str, unit_scale: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UnitScalesCollection.get_instance()
        return await collection.update_unit_scale_by_id(unit_scale_id, unit_scale)

    async def delete_unit_scale_by_id(self, unit_scale_id: str) -> dict[str, Any] | None:
        collection = UnitScalesCollection.get_instance()
        return await collection.delete_unit_scale_by_id(unit_scale_id)
