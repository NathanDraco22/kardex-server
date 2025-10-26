from tools import TimeTools, UuidTool
from .data.expiration_logs_datasource import ExpirationLogsDataSource
from .models.expiration_log_model import (
    CreateExpirationLog,
    UpdateExpirationLog,
    ExpirationLogInDb,
)


class ExpirationLogsRepository:
    def __init__(self, expiration_logs_ds: ExpirationLogsDataSource):
        self.expiration_logs_ds = expiration_logs_ds

    async def create_expiration_log(
        self, create_expiration_log: CreateExpirationLog
    ) -> ExpirationLogInDb:
        new_expiration_log = ExpirationLogInDb(
            **create_expiration_log.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.expiration_logs_ds.create_expiration_log(
            new_expiration_log.model_dump()
        )

        return new_expiration_log

    async def get_all_expiration_logs(self, **kwargs) -> list[ExpirationLogInDb]:
        results = await self.expiration_logs_ds.get_all_expiration_logs(**kwargs)
        models = [ExpirationLogInDb.model_validate(result) for result in results]
        return models

    async def get_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> ExpirationLogInDb | None:
        result = await self.expiration_logs_ds.get_expiration_log_by_id(
            expiration_log_id
        )

        if result is None:
            return None

        return ExpirationLogInDb.model_validate(result)

    async def update_expiration_log_by_id(
        self, expiration_log_id: str, expiration_log: UpdateExpirationLog
    ) -> ExpirationLogInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> ExpirationLogInDb | None:
        result = await self.expiration_logs_ds.delete_expiration_log_by_id(
            expiration_log_id
        )

        if result is None:
            return None

        return ExpirationLogInDb.model_validate(result)
