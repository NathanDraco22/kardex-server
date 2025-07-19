from fastapi import HTTPException, status

from repos.v1.branches import (
    CreateBranch,
    BranchInDb,
    BranchesRepository,
    BranchesDataSource,
)


class BranchesController:
    def __init__(self, branches_repo: BranchesRepository) -> None:
        self.branches_repo = branches_repo

    async def create_branch(self, body: CreateBranch) -> BranchInDb:
        return await self.branches_repo.create_branch(body)

    async def get_all_branches(self) -> list[BranchInDb]:
        branches = await self.branches_repo.get_all_branches()
        return branches

    async def get_branch_by_id(self, branch_id: str) -> BranchInDb:
        branch = await self.branches_repo.get_branch_by_id(branch_id)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )
        return branch


branches_controller = BranchesController(
    branches_repo=BranchesRepository(
        branches_ds=BranchesDataSource(),
    ),
)
