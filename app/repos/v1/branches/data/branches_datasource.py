from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import BranchesCollection


class BranchesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_branch(self, branch: dict[str, Any]) -> dict[str, Any]:
        collection = BranchesCollection()
        await collection.create_branch(branch)
        return branch

    async def get_all_branches(self) -> list[dict[str, Any]]:
        collection = BranchesCollection()
        return await collection.fetch_all_branches()

    async def get_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = BranchesCollection()
        return await collection.fetch_branch_by_id(branch_id)

    async def update_branch_by_id(
        self, branch_id: str, branch: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = BranchesCollection()
        return await collection.update_branch_by_id(branch_id, branch)

    async def delete_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = BranchesCollection()
        return await collection.delete_branch_by_id(branch_id)
