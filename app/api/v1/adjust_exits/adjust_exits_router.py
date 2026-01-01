from fastapi import APIRouter, Depends
from api.common.query_params import AdjustQueryParams
from repos.v1.adjust_exits import CreateAdjustExit, AdjustExitInDb

from responses.v1 import ListResponse

from .adjust_exits_controller import adjust_exits_controller


adjust_exits_router = APIRouter(tags=["adjust_exitsV1"])


@adjust_exits_router.post("")
async def create_adjust_exit(body: CreateAdjustExit) -> AdjustExitInDb:
    return await adjust_exits_controller.create_adjust_exit(body)


@adjust_exits_router.get("")
async def get_all_adjust_exits(
    query: AdjustQueryParams = Depends(),
) -> ListResponse[AdjustExitInDb]:
    return await adjust_exits_controller.get_all_adjust_exits(query)


@adjust_exits_router.get("/{adjust_exit_id}")
async def get_adjust_exit_by_id(adjust_exit_id: str) -> AdjustExitInDb:
    return await adjust_exits_controller.get_adjust_exit_by_id(adjust_exit_id)


@adjust_exits_router.get("/{branch_id}/{doc_number}")
async def get_adjust_exit_by_doc_number(
    doc_number: str, branch_id: str
) -> AdjustExitInDb:
    return await adjust_exits_controller.get_adjust_exit_by_doc_number(
        doc_number, branch_id
    )
