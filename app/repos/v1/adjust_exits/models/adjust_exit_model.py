from typing import Literal
from pydantic import BaseModel
from repos.v1.common.models import UserInfo, ExitItem


AdjustExitType = Literal["adjust", "loss", "devolution"]


class BaseAdjustExit(BaseModel):
    docNumber: str = ""
    branchId: str
    description: str = ""
    type: AdjustExitType
    items: list[ExitItem]
    createdBy: UserInfo


class CreateAdjustExit(BaseAdjustExit):
    pass


class UpdateAdjustExit(BaseModel):
    pass


class AdjustExitInDb(BaseAdjustExit):
    id: str
    createdAt: int
    updatedAt: int | None = None
