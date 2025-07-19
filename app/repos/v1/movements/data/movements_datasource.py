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

    async def get_movements_by_product_and_branch(
        self, product_id: str, branch_id: str, start_date: int, end_date: int
    ) -> list[dict[str, Any]]:
        collection = MovementsCollection()
        res = await collection.fetch_movements_by_product_and_branch(
            product_id, branch_id, start_date, end_date
        )
        return res

    async def get_movement_by_id(self, movement_id: str) -> dict[str, Any] | None:
        collection = MovementsCollection()
        return await collection.fetch_movement_by_id(movement_id)
