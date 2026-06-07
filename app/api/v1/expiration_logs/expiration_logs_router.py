from fastapi import APIRouter, Depends
from kardex.repos.v1.expiration_logs import (
    CreateExpirationLog,
    ExpirationLogInDb,
)

from app_middleware import auth_middleware

from responses.v1 import ListResponse

from .expiration_logs_controller import expiration_logs_controller
from kardex.repos.v1.common.filter_params import ExpirationLogFilterParams


expiration_logs_router = APIRouter(
    tags=["expiration_logsV1"], dependencies=[Depends(auth_middleware)]
)


@expiration_logs_router.post("")
async def create_expiration_log(body: CreateExpirationLog) -> ExpirationLogInDb:
    return await expiration_logs_controller.create_expiration_log(body)


@expiration_logs_router.get("")
async def get_all_expiration_logs(
    params: ExpirationLogFilterParams = Depends(),
) -> ListResponse[ExpirationLogInDb]:
    return await expiration_logs_controller.get_all_expiration_logs(params)


@expiration_logs_router.get("/{expiration_log_id}")
async def get_expiration_log_by_id(expiration_log_id: str) -> ExpirationLogInDb:
    return await expiration_logs_controller.get_expiration_log_by_id(expiration_log_id)


@expiration_logs_router.delete("/{expiration_log_id}")
async def delete_expiration_log_by_id(expiration_log_id: str) -> ExpirationLogInDb:
    return await expiration_logs_controller.delete_expiration_log_by_id(
        expiration_log_id
    )


@expiration_logs_router.get("/near/{branch_id}")
async def has_near_expiration_date(branch_id: str) -> dict[str, bool]:
    return await expiration_logs_controller.has_near_expiration_date(branch_id)
