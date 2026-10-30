from pydantic import BaseModel

from kardex.repos.v1.common.models.user_info import UserInfo


class OrderInfo(BaseModel):
    id: str = ""
    docNumber: str = ""
    createdAt: int
    createdBy: UserInfo
