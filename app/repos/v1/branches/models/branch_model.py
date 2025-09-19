from pydantic import BaseModel


class BaseBranch(BaseModel):
    name: str
    description: str = ""
    pass


class CreateBranch(BaseBranch):
    pass


class UpdateBranch(BaseModel):
    name: str | None = None
    description: str | None = None


class BranchInDb(BaseBranch):
    id: str
    createdAt: int
    updatedAt: int | None = None
