from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import MovementsCollection


class MovementsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_movement(self, movement: dict[str, Any]) -> dict[str, Any]:
        collection = MovementsCollection()
        await collection.create_movement(movement)
        return movement

    async def get_all_movements(self) -> list[dict[str, Any]]:
        collection = MovementsCollection()
        return await collection.fetch_all_movements()

    async def get_movement_by_id(self, movement_id: str) -> dict[str, Any] | None:
        collection = MovementsCollection()
        return await collection.fetch_movement_by_id(movement_id)
