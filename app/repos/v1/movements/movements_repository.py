import uuid
from tools import TimeTools

from .data.movements_datasource import MovementsDataSource
from .models.movement_model import CreateMovement, MovementInDb


class MovementsRepository:
    def __init__(self, movements_ds: MovementsDataSource):
        self.movements_ds = movements_ds

    async def create_movement(self, create_movement: CreateMovement) -> MovementInDb:
        new_movement = MovementInDb(
            id=str(uuid.uuid4()),
            created_at=TimeTools.get_now_in_milliseconds(),
            **create_movement.model_dump(),
        )

        await self.movements_ds.create_movement(new_movement.model_dump())
        return new_movement

    async def get_all_movements(self) -> list[MovementInDb]:
        results = await self.movements_ds.get_all_movements()
        models = [MovementInDb.model_validate(result) for result in results]
        return models

    async def get_movements_by_product_and_branch(
        self, product_id: str, branch_id: str, start_date: int, end_date: int
    ) -> list[MovementInDb]:
        results = await self.movements_ds.get_movements_by_product_and_branch(
            product_id, branch_id, start_date, end_date
        )
        models = [MovementInDb.model_validate(result) for result in results]
        return models

    async def get_movement_by_id(self, movement_id: str) -> MovementInDb | None:
        result = await self.movements_ds.get_movement_by_id(movement_id)

        if result is None:
            return None

        return MovementInDb.model_validate(result)
