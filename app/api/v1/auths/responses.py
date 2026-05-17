from pydantic import BaseModel
from kardex.repos.v1.users import UserInDbWithRole


class LoginResponse(BaseModel):
    user: UserInDbWithRole
    accessToken: str


class ServinStatusResponese(BaseModel):
    nickname: str
    isActive: bool
    isMultiBranch: bool
