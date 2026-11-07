from fastapi import HTTPException, status
from kardex.repos.v1.unit_scales import (
    CreateUnitScale,
    UpdateUnitScale,
    UnitScaleInDb,
    UnitScalesRepository,
)
from responses.v1 import ListResponse


class UnitScalesController:
    def __init__(self, unit_scales_repo: UnitScalesRepository) -> None:
        self.unit_scales_repo = unit_scales_repo

    async def create_unit_scale(self, body: CreateUnitScale) -> UnitScaleInDb:
        return await self.unit_scales_repo.create_unit_scale(body)

    async def get_all_unit_scales(self) -> ListResponse[UnitScaleInDb]:
        unit_scales = await self.unit_scales_repo.get_all_unit_scales()
        return ListResponse(
            count=len(unit_scales),
            data=unit_scales,
        )

    async def get_unit_scale_by_id(self, unit_scale_id: str) -> UnitScaleInDb:
        unit_scale = await self.unit_scales_repo.get_unit_scale_by_id(unit_scale_id)
        if unit_scale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnitScale not found",
            )
        return unit_scale

    async def update_unit_scale_by_id(
        self, unit_scale_id: str, body: UpdateUnitScale
    ) -> UnitScaleInDb:
        updated_unit_scale = await self.unit_scales_repo.update_unit_scale_by_id(
            unit_scale_id, body
        )
        if updated_unit_scale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnitScale not found",
            )
        return updated_unit_scale

    async def delete_unit_scale_by_id(self, unit_scale_id: str) -> UnitScaleInDb:
        deleted_unit_scale = await self.unit_scales_repo.delete_unit_scale_by_id(
            unit_scale_id
        )
        if deleted_unit_scale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnitScale not found",
            )
        return deleted_unit_scale


unit_scales_controller = UnitScalesController(
    unit_scales_repo=UnitScalesRepository.get_instance(),
)
