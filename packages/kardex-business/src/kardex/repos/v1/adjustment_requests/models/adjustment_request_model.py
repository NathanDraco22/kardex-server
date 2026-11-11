from typing import Literal

from pydantic import BaseModel, Field

from kardex.repos.v1.common.models import UserInfo


AdjustmentRequestStatus = Literal["pending", "approved", "cancelled"]


class CreateAdjustmentRequestItem(BaseModel):
    productId: str
    productName: str
    code: str | None = None
    brandName: str | None = None
    unitName: str | None = None
    conversionFactor: int = 1
    standardUnitName: str | None = None
    standardUnitFactor: int | None = None
    countedQuantity: int = Field(..., ge=0)
    cost: int = Field(..., ge=0)


class AdjustmentRequestItem(CreateAdjustmentRequestItem):
    systemStock: int
    difference: int
    subtotal: int


class BaseAdjustmentRequest(BaseModel):
    docNumber: str = ""
    branchId: str
    description: str = ""
    items: list[CreateAdjustmentRequestItem]
    createdBy: UserInfo


class CreateAdjustmentRequest(BaseAdjustmentRequest):
    pass


class UpdateAdjustmentRequest(BaseModel):
    description: str | None = None
    items: list[CreateAdjustmentRequestItem] | None = None


class AdjustmentRequestInDb(BaseAdjustmentRequest):
    id: str
    status: AdjustmentRequestStatus = "pending"
    items: list[AdjustmentRequestItem]
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
    approvedBy: UserInfo | None = None
    approvedAt: int | None = None
    cancelledBy: UserInfo | None = None
    cancelledAt: int | None = None
    cancellationReason: str | None = None
    adjustEntryId: str | None = None
    adjustEntryDocNumber: str | None = None
    adjustExitId: str | None = None
    adjustExitDocNumber: str | None = None
    entryTotal: int = 0
    exitTotal: int = 0


class ApproveAdjustmentRequest(BaseModel):
    approvedBy: UserInfo


class CancelAdjustmentRequest(BaseModel):
    cancelledBy: UserInfo
    reason: str | None = None
