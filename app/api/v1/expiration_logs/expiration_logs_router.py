from fastapi import APIRouter

from repos.v1.expiration_logs import (
    CreateExpirationLog,
    ExpirationLogInDb,
)


from responses.v1 import ListResponse

from .expiration_logs_controller import expiration_logs_controller


expiration_logs_router = APIRouter(tags=["expiration_logsV1"])


@expiration_logs_router.post("")
async def create_expiration_log(body: CreateExpirationLog) -> ExpirationLogInDb:
    return await expiration_logs_controller.create_expiration_log(body)


@expiration_logs_router.get("")
async def get_all_expiration_logs() -> ListResponse[ExpirationLogInDb]:
    return await expiration_logs_controller.get_all_expiration_logs()


@expiration_logs_router.get("/{expiration_log_id}")
async def get_expiration_log_by_id(expiration_log_id: str) -> ExpirationLogInDb:
    return await expiration_logs_controller.get_expiration_log_by_id(expiration_log_id)


@expiration_logs_router.delete("/{expiration_log_id}")
async def delete_expiration_log_by_id(expiration_log_id: str) -> ExpirationLogInDb:
    return await expiration_logs_controller.delete_expiration_log_by_id(
        expiration_log_id
    )
