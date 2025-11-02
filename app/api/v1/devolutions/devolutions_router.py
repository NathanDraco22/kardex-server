from fastapi import APIRouter, Depends

from repos.v1.devolutions import CreateDevolution, DevolutionInDb
from responses.v1 import ListResponse

from .devolutions_controller import devolutions_controller
from .devolution_query_param import DevolutionQueryParams

devolutions_router = APIRouter(tags=["devolutionsV1"])


@devolutions_router.post("")
async def create_devolution(body: CreateDevolution) -> DevolutionInDb:
    return await devolutions_controller.create_devolution(body)


@devolutions_router.get("")
async def get_all_devolutions(
    params: DevolutionQueryParams = Depends(),
) -> ListResponse[DevolutionInDb]:
    return await devolutions_controller.get_all_devolutions(params)


@devolutions_router.get("/{devolution_id}")
async def get_devolution_by_id(devolution_id: str) -> DevolutionInDb:
    return await devolutions_controller.get_devolution_by_id(devolution_id)


@devolutions_router.patch("/confirm/{devolution_id}")
async def confirm_devolution_by_id(devolution_id: str) -> DevolutionInDb:
    return await devolutions_controller.confirm_develution(devolution_id)


@devolutions_router.patch("/confirm-anon/{devolution_id}")
async def confirm_anon_devolution_by_id(devolution_id: str) -> DevolutionInDb:
    return await devolutions_controller.confirm_anon_devolution(devolution_id)


@devolutions_router.patch("/cancel/{devolution_id}")
async def cancel_devolution_by_id(devolution_id: str) -> DevolutionInDb:
    return await devolutions_controller.cancel_devolution_by_id(devolution_id)


@devolutions_router.delete("/{devolution_id}")
async def delete_devolution_by_id(devolution_id: str) -> DevolutionInDb:
    return await devolutions_controller.delete_devolution_by_id(devolution_id)
