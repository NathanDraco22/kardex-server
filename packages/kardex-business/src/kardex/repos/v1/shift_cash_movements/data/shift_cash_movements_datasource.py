from typing import Any

from kardex.services.mongo_collections.v1 import ShiftCashMovementsCollection


class ShiftCashMovementsDataSource:

    async def create_shift_cash_movement(
        self, movement: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        collection = ShiftCashMovementsCollection.get_instance()
        await collection.create_shift_cash_movement(movement, session=session)
        return movement

    async def get_all_shift_cash_movements(self, **kwargs) -> list[dict[str, Any]]:
        collection = ShiftCashMovementsCollection.get_instance()
        return await collection.fetch_all_shift_cash_movements(**kwargs)

    async def get_shift_cash_movement_by_id(
        self, movement_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftCashMovementsCollection.get_instance()
        return await collection.fetch_shift_cash_movement_by_id(
            movement_id, session=session
        )

    async def update_shift_cash_movement_by_id(
        self, movement_id: str, movement: dict[str, Any], session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftCashMovementsCollection.get_instance()
        return await collection.update_shift_cash_movement_by_id(
            movement_id, movement, session=session
        )

    async def delete_shift_cash_movement_by_id(
        self, movement_id: str, deleted_at: int, session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftCashMovementsCollection.get_instance()
        return await collection.soft_delete_shift_cash_movement_by_id(
            movement_id, deleted_at, session=session
        )

    async def get_type_totals_by_shift(self, shift_id: str) -> list[dict[str, Any]]:
        collection = ShiftCashMovementsCollection.get_instance()
        return await collection.get_type_totals_by_shift(shift_id)
