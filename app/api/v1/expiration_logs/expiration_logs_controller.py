from fastapi import HTTPException, status

from kardex.repos.v1.expiration_logs import (
    CreateExpirationLog,
    UpdateExpirationLog,
    ExpirationLogInDb,
    ExpirationLogsRepository,
    ExpirationLogsDataSource,
)

from responses.v1 import ListResponse
from tools import TimeTools

from .query_params import ExpirationLogQueryParams


class ExpirationLogsController:
    def __init__(self, expiration_logs_repo: ExpirationLogsRepository) -> None:
        self.expiration_logs_repo = expiration_logs_repo

    async def create_expiration_log(
        self, body: CreateExpirationLog
    ) -> ExpirationLogInDb:
        return await self.expiration_logs_repo.create_expiration_log(body)

    async def get_all_expiration_logs(
        self, params: ExpirationLogQueryParams
    ) -> ListResponse[ExpirationLogInDb]:
        expiration_logs = await self.expiration_logs_repo.get_all_expiration_logs(
            **params.model_dump()
        )
        return ListResponse(
            count=len(expiration_logs),
            data=expiration_logs,
        )

    async def get_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> ExpirationLogInDb:
        expiration_log = await self.expiration_logs_repo.get_expiration_log_by_id(
            expiration_log_id
        )
        if expiration_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpirationLog not found",
            )
        return expiration_log

    async def update_expiration_log_by_id(
        self, expiration_log_id: str, body: UpdateExpirationLog
    ) -> ExpirationLogInDb:
        updated_expiration_log = (
            await self.expiration_logs_repo.update_expiration_log_by_id(
                expiration_log_id, body
            )
        )
        if updated_expiration_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpirationLog not found",
            )
        return updated_expiration_log

    async def delete_expiration_log_by_id(
        self, expiration_log_id: str
    ) -> ExpirationLogInDb:
        deleted_expiration_log = (
            await self.expiration_logs_repo.delete_expiration_log_by_id(
                expiration_log_id
            )
        )
        if deleted_expiration_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExpirationLog not found",
            )
        return deleted_expiration_log

    async def has_near_expiration_date(self, branch_id: str) -> dict[str, bool]:
        target_date = TimeTools.get_now_in_100days_in_milliseconds()
        has_expiration = await self.expiration_logs_repo.has_near_expiration_date(
            target_date, branch_id
        )
        return {"hasExpiration": has_expiration}


expiration_logs_controller = ExpirationLogsController(
    expiration_logs_repo=ExpirationLogsRepository(
        expiration_logs_ds=ExpirationLogsDataSource(),
    ),
)
