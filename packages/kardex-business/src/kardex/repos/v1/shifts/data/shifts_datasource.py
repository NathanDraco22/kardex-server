from typing import Any

from kardex.services.mongo_collections.v1 import ShiftsCollection


class ShiftsDataSource:

    async def create_shift(self, shift: dict[str, Any], session: Any = None) -> dict[str, Any]:
        collection = ShiftsCollection.get_instance()
        await collection.create_shift(shift, session=session)
        return shift

    async def get_all_shifts(self, **kwargs) -> list[dict[str, Any]]:
        collection = ShiftsCollection.get_instance()
        return await collection.fetch_all_shifts(**kwargs)

    async def get_shift_by_id(
        self, shift_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftsCollection.get_instance()
        return await collection.fetch_shift_by_id(shift_id, session=session)

    async def get_active_shift_by_user(
        self, user_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftsCollection.get_instance()
        return await collection.fetch_active_shift_by_user(user_id, session=session)

    async def update_shift_by_id(
        self, shift_id: str, shift: dict[str, Any], session: Any = None
    ) -> dict[str, Any] | None:
        collection = ShiftsCollection.get_instance()
        return await collection.update_shift_by_id(shift_id, shift, session=session)
