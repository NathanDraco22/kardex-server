from pydantic import BaseModel


class BaseBranch(BaseModel):
    name: str
    description: str | None = None
    pass


class CreateBranch(BaseBranch):
    pass


class UpdateBranch(BaseModel):
    name: str | None = None
    description: str | None = None


class BranchInDb(BaseBranch):
    id: str
    created_at: int
    updated_at: int
