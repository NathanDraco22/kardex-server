from fastapi import APIRouter, Request, Response

from repos.v1.branches import CreateBranch, UpdateBranch, BranchInDb
from responses.v1 import ListResponse

from tools import EtagTool, NotModified

from .branches_controller import branches_controller


branches_router = APIRouter(tags=["branchesV1"])


@branches_router.post("")
async def create_branch(body: CreateBranch) -> BranchInDb:
    return await branches_controller.create_branch(body)


@branches_router.get("")
async def get_all_branches(
    request: Request, response: Response
) -> ListResponse[BranchInDb]:
    match_value = request.headers.get("If-None-Match")
    current_tag = EtagTool().get_branches_etag()
    current_tag_value = current_tag.value if current_tag is not None else None

    if match_value == current_tag_value and current_tag is not None:
        raise NotModified

    result = await branches_controller.get_all_branches()

    if current_tag is not None:
        response.headers["ETag"] = current_tag.value

    return result


@branches_router.get("/{branch_id}")
async def get_branch_by_id(
    branch_id: str, req: Request, response: Response
) -> BranchInDb:
    match_value = req.headers.get("If-None-Match")

    current_tag = EtagTool().get_etag(branch_id)
    current_tag_value = current_tag.value if current_tag is not None else None

    if match_value == current_tag_value and current_tag is not None:
        raise NotModified

    result = await branches_controller.get_branch_by_id(branch_id)

    if current_tag is not None:
        response.headers["ETag"] = current_tag.value

    return result


@branches_router.patch("/{branch_id}")
async def update_branch_by_id(branch_id: str, body: UpdateBranch) -> BranchInDb:
    return await branches_controller.update_branch_by_id(branch_id, body)


@branches_router.delete("/{branch_id}")
async def delete_branch_by_id(branch_id: str) -> BranchInDb:
    return await branches_controller.delete_branch_by_id(branch_id)
