from typing import Literal

from pydantic import BaseModel, Field

from kardex.repos.v1.common.models import UserInfo

CashMovementType = Literal["in", "out"]


class BaseShiftCashMovement(BaseModel):
    branchId: str
    shiftId: str
    docNumber: str = ""
    type: CashMovementType
    amount: int = Field(gt=0)
    reason: str = Field(min_length=1)
    registerAsExpense: bool = False
    expenseCategory: str | None = None
    expenseId: str | None = None
    createdBy: UserInfo
    isDeleted: bool = False
    deletedAt: int | None = None


class CreateShiftCashMovement(BaseModel):
    branchId: str
    shiftId: str
    type: CashMovementType
    amount: int = Field(gt=0)
    reason: str = Field(min_length=1)
    registerAsExpense: bool = False
    expenseCategory: str | None = None
    createdBy: UserInfo


class UpdateShiftCashMovement(BaseModel):
    reason: str | None = Field(default=None, min_length=1)


class ShiftCashMovementInDb(BaseShiftCashMovement):
    id: str
    createdAt: int
    updatedAt: int | None = None
