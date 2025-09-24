from pydantic import BaseModel
from repos.v1.users import UserInDbWithRole


class LoginResponse(BaseModel):
    user: UserInDbWithRole
    access_token: str
