from kardex.tools import UuidTool, TimeTools

from .data.unit_scales_datasource import UnitScalesDataSource
from .models.unit_scale_model import CreateUnitScale, UpdateUnitScale, UnitScaleInDb


class UnitScalesRepository:

    _instance: "UnitScalesRepository | None" = None

    def __init__(self, unit_scales_ds: UnitScalesDataSource):
        self.unit_scales_ds = unit_scales_ds

    @classmethod
    def get_instance(cls) -> "UnitScalesRepository":
        if cls._instance is None:
            cls._instance = cls(UnitScalesDataSource())
        return cls._instance

    async def create_unit_scale(self, create_unit_scale: CreateUnitScale) -> UnitScaleInDb:
        new_unit_scale = UnitScaleInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_unit_scale.model_dump(),
        )

        await self.unit_scales_ds.create_unit_scale(new_unit_scale.model_dump())
        return new_unit_scale

    async def get_all_unit_scales(self) -> list[UnitScaleInDb]:
        results = await self.unit_scales_ds.get_all_unit_scales()
        models = [UnitScaleInDb.model_validate(result) for result in results]
        return models

    async def get_unit_scale_by_id(self, unit_scale_id: str) -> UnitScaleInDb | None:
        result = await self.unit_scales_ds.get_unit_scale_by_id(unit_scale_id)
        if result is None:
            return None
        return UnitScaleInDb.model_validate(result)

    async def update_unit_scale_by_id(
        self, unit_scale_id: str, unit_scale: UpdateUnitScale
    ) -> UnitScaleInDb | None:
        update_data = unit_scale.model_dump(exclude_unset=True)
        update_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.unit_scales_ds.update_unit_scale_by_id(unit_scale_id, update_data)
        if result is None:
            return None
        return UnitScaleInDb.model_validate(result)

    async def delete_unit_scale_by_id(self, unit_scale_id: str) -> UnitScaleInDb | None:
        result = await self.unit_scales_ds.delete_unit_scale_by_id(unit_scale_id)
        if result is None:
            return None
        return UnitScaleInDb.model_validate(result)
