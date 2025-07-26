from fastapi import HTTPException, status

from repos.v1.units import (
    CreateUnit,
    UpdateUnit,
    UnitInDb,
    UnitsRepository,
    UnitsDataSource,
)

from responses.v1 import ListResponse


class UnitsController:
    def __init__(self, units_repo: UnitsRepository) -> None:
        self.units_repo = units_repo

    async def create_unit(self, body: CreateUnit) -> UnitInDb:
        return await self.units_repo.create_unit(body)

    async def get_all_units(self) -> ListResponse[UnitInDb]:
        units = await self.units_repo.get_all_units()
        return ListResponse(
            count=len(units),
            data=units,
        )

    async def get_unit_by_id(self, unit_id: str) -> UnitInDb:
        unit = await self.units_repo.get_unit_by_id(unit_id)
        if unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found",
            )
        return unit

    async def update_unit_by_id(self, unit_id: str, body: UpdateUnit) -> UnitInDb:
        updated_unit = await self.units_repo.update_unit_by_id(unit_id, body)
        if updated_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found",
            )
        return updated_unit

    async def delete_unit_by_id(self, unit_id: str) -> UnitInDb:
        deleted_unit = await self.units_repo.delete_unit_by_id(unit_id)
        if deleted_unit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found",
            )
        return deleted_unit


units_controller = UnitsController(
    units_repo=UnitsRepository(
        units_ds=UnitsDataSource(),
    ),
)
