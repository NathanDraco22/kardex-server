from repos.v1.branches import BranchInDb, BranchesRepository, BranchesDataSource


class BranchesTool:
    _instance: "BranchesTool|None" = None

    __branches_repo = BranchesRepository(BranchesDataSource())

    _branches: list[BranchInDb] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BranchesTool, cls).__new__(cls)
        return cls._instance

    async def refresh_current_branches(self):
        branches = await self.__branches_repo.get_all_branches()
        self._branches = branches

    def get_branch_by_id(self, branch_id: str) -> BranchInDb | None:
        for branch in self._branches:
            if branch.id == branch_id:
                return branch
