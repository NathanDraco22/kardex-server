from tools import UuidTool, TimeTools

from .data.units_datasource import UnitsDataSource
from .models.unit_model import CreateUnit, UpdateUnit, UnitInDb


class UnitsRepository:
    def __init__(self, units_ds: UnitsDataSource):
        self.units_ds = units_ds

    async def create_unit(self, create_unit: CreateUnit) -> UnitInDb:
        new_unit = UnitInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_unit.model_dump(),
        )

        await self.units_ds.create_unit(new_unit.model_dump())

        return new_unit

    async def get_all_units(self) -> list[UnitInDb]:
        results = await self.units_ds.get_all_units()
        models = [UnitInDb.model_validate(result) for result in results]
        return models

    async def get_unit_by_id(self, unit_id: str) -> UnitInDb | None:
        result = await self.units_ds.get_unit_by_id(unit_id)

        if result is None:
            return None

        return UnitInDb.model_validate(result)

    async def update_unit_by_id(
        self, unit_id: str, unit: UpdateUnit
    ) -> UnitInDb | None:
        update_unit_data = unit.model_dump(exclude_unset=True)

        update_unit_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.units_ds.update_unit_by_id(unit_id, update_unit_data)

        if result is None:
            return None

        return UnitInDb.model_validate(result)

    async def delete_unit_by_id(self, unit_id: str) -> UnitInDb | None:
        result = await self.units_ds.delete_unit_by_id(unit_id)

        if result is None:
            return None

        return UnitInDb.model_validate(result)
