from pydantic import BaseModel
from repos.v1.users import UserInDbWithRole


class LoginResponse(BaseModel):
    user: UserInDbWithRole
    accessToken: str


class ServinStatusResponese(BaseModel):
    isActive: bool
    isMultiBranch: bool
