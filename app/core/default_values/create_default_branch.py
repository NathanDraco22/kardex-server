from repos.v1.branches import BranchInDb
from services.mongo_collections.v1 import BranchesCollection
from tools import TimeTools

ORIGIN_BRANCH_ID = "ORIGIN_BRANCH"
origin_branch_name = "Origen"


async def create_default_branch() -> BranchInDb:
    new_branch = BranchInDb(
        id=ORIGIN_BRANCH_ID,
        name=origin_branch_name,
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await BranchesCollection().create_branch_if_absent(
        ORIGIN_BRANCH_ID, new_branch.model_dump()
    )

    return new_branch
