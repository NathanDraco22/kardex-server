from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import UnitsCollection


class UnitsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_unit(self, unit: dict[str, Any]) -> dict[str, Any]:
        collection = UnitsCollection()
        await collection.create_unit(unit)
        return unit

    async def get_all_units(self) -> list[dict[str, Any]]:
        collection = UnitsCollection()
        return await collection.fetch_all_units()

    async def get_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = UnitsCollection()
        return await collection.fetch_unit_by_id(unit_id)

    async def update_unit_by_id(
        self, unit_id: str, unit: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UnitsCollection()
        return await collection.update_unit_by_id(unit_id, unit)

    async def delete_unit_by_id(self, unit_id: str) -> dict[str, Any] | None:
        collection = UnitsCollection()
        return await collection.delete_unit_by_id(unit_id)
