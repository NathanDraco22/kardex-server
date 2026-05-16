from .data.adjust_exits_datasource import AdjustExitsDataSource
from .models.adjust_exit_model import CreateAdjustExit, UpdateAdjustExit, AdjustExitInDb


class AdjustExitsRepository:
    def __init__(self, adjust_exits_ds: AdjustExitsDataSource):
        self.adjust_exits_ds = adjust_exits_ds

    async def create_adjust_exit(
        self, create_adjust_exit: CreateAdjustExit
    ) -> AdjustExitInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_adjust_exits(self, **kwargs) -> list[AdjustExitInDb]:
        results = await self.adjust_exits_ds.get_all_adjust_exits(**kwargs)
        models = [AdjustExitInDb.model_validate(result) for result in results]
        return models

    async def get_adjust_exit_by_id(self, adjust_exit_id: str) -> AdjustExitInDb | None:
        result = await self.adjust_exits_ds.get_adjust_exit_by_id(adjust_exit_id)

        if result is None:
            return None

        return AdjustExitInDb.model_validate(result)

    async def get_adjust_exit_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> AdjustExitInDb | None:
        result = await self.adjust_exits_ds.get_adjust_exit_by_doc_number(
            doc_number, branch_id
        )

        if result is None:
            return None

        return AdjustExitInDb.model_validate(result)

    async def update_adjust_exit_by_id(
        self, adjust_exit_id: str, adjust_exit: UpdateAdjustExit
    ) -> AdjustExitInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_adjust_exit_by_id(
        self, adjust_exit_id: str
    ) -> AdjustExitInDb | None:
        result = await self.adjust_exits_ds.delete_adjust_exit_by_id(adjust_exit_id)

        if result is None:
            return None

        return AdjustExitInDb.model_validate(result)
