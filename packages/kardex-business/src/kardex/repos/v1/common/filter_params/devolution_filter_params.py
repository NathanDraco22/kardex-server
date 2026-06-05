from pydantic import BaseModel
from kardex.repos.v1.devolutions.models.devolution_model import DevolutionStatus

class DevolutionFilterParams(BaseModel):
    branchId: str | None = None
    clientId: str | None = None
    status: DevolutionStatus | None = None
