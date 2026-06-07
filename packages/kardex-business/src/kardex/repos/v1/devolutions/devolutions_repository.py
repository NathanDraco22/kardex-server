from kardex.tools import TimeTools, UuidTool
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.models.history_params import HistoryClientParams
from kardex.repos.v1.common.filter_params import DevolutionFilterParams

from .data.devolutions_datasource import DevolutionsDataSource
from .models.devolution_model import CreateDevolution, UpdateDevolution, DevolutionInDb

class DevolutionsRepository:
    _instance: "DevolutionsRepository | None" = None

    def __init__(self, devolutions_ds: DevolutionsDataSource):
        self.devolutions_ds = devolutions_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DevolutionsRepository(
                devolutions_ds=DevolutionsDataSource()
            )
        return cls._instance

    async def create_devolution(
        self, create_devolution: CreateDevolution
    ) -> DevolutionInDb:
        if not create_devolution.docNumber:
            create_devolution.docNumber = (
                await CounterManager().next_devolution_number()
            )
        new_devolution = DevolutionInDb(
            **create_devolution.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.devolutions_ds.create_devolution(new_devolution.model_dump())

        return new_devolution

    async def get_all_devolutions(
        self, params: DevolutionFilterParams
    ) -> list[DevolutionInDb]:
        results = await self.devolutions_ds.get_all_devolutions(
            **params.model_dump(exclude_unset=True)
        )
        models = [DevolutionInDb.model_validate(result) for result in results]
        return models

    async def get_all_active_devolutions(
        self, params: DevolutionFilterParams
    ) -> list[DevolutionInDb]:
        results = await self.devolutions_ds.get_all_active_devolutions(
            **params.model_dump(exclude_unset=True)
        )
        models = [DevolutionInDb.model_validate(result) for result in results]
        return models

    async def get_devolution_by_id(self, devolution_id: str) -> DevolutionInDb | None:
        result = await self.devolutions_ds.get_devolution_by_id(devolution_id)

        if result is None:
            return None

        return DevolutionInDb.model_validate(result)

    async def get_devolution_by_invoice_id(
        self, invoice_id: str, client_id: str | None
    ) -> list[DevolutionInDb]:
        result = await self.devolutions_ds.get_devolutions_by_invoice_id(
            invoice_id, client_id
        )

        return [DevolutionInDb.model_validate(devolution) for devolution in result]

    async def get_devolution_by_doc_number(
        self, doc_number: str
    ) -> DevolutionInDb | None:
        result = await self.devolutions_ds.get_devolution_by_doc_number(doc_number)

        if result is None:
            return None

        return DevolutionInDb.model_validate(result)

    async def update_devolution_by_id(
        self, devolution_id: str, devolution: UpdateDevolution
    ) -> DevolutionInDb | None:
        updated_data = devolution.model_dump(exclude_unset=True)

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.devolutions_ds.update_devolution_by_id(
            devolution_id, updated_data
        )

        if result is None:
            return None

        return DevolutionInDb.model_validate(result)

    async def delete_devolution_by_id(
        self, devolution_id: str
    ) -> DevolutionInDb | None:
        result = await self.devolutions_ds.delete_devolution_by_id(devolution_id)

        if result is None:
            return None

        return DevolutionInDb.model_validate(result)

    async def get_devolution_history(
        self, params: HistoryClientParams
    ) -> list[DevolutionInDb]:
        params_data = params.to_query_params()
        results = await self.devolutions_ds.get_devolution_history(**params_data)
        models = [DevolutionInDb.model_validate(result) for result in results]
        return models
