from pydantic import BaseModel
from kardex.repos.v1.common.models import UserInfo


class ResetBranchInventoryRequest(BaseModel):
    branchId: str
    branchNameConfirm: str
    description: str = "Reinicio de inventario a 0 (Zona de Peligro)"
    createdBy: UserInfo


class ResetBranchInventoryResponse(BaseModel):
    message: str
    branchId: str
    docNumber: str = ""
    adjustExitId: str = ""
    adjustedProductsCount: int = 0
    totalQuantityRemoved: int = 0
