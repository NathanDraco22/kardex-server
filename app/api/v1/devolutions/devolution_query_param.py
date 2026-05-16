from pydantic import BaseModel
from kardex.repos.v1.devolutions.models.devolution_model import DevolutionStatus


class DevolutionQueryParams(BaseModel):
    branchId: str | None = None
    clientId: str | None = None
    status: DevolutionStatus | None = None
