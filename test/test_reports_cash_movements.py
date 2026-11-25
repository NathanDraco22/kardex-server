from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.reports.reports_controller import ReportsController
from kardex.repos.v1.common.filter_params import (
    ShiftCashMovementFilterParams,
    TotalsFilterParams,
)
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.shift_cash_movements import ShiftCashMovementInDb


@pytest.mark.asyncio
async def test_get_total_results_includes_shift_cash_movements() -> None:
    controller = ReportsController(
        daily_summaries_repo=MagicMock(),
        executive_summaries_repo=MagicMock(),
    )
    controller.invoices_repo = MagicMock()
    controller.invoices_repo.get_totals_invoices_by_payment_type = AsyncMock(
        return_value=[]
    )
    controller.invoices_repo.get_all_invoices = AsyncMock(return_value=[])
    controller.receipts_repo = MagicMock()
    controller.receipts_repo.get_totals_from_receipts_by_payment_method = AsyncMock(
        return_value=[]
    )
    controller.receipts_repo.get_all_receipts = AsyncMock(return_value=[])
    controller.expenses_repo = MagicMock()
    controller.expenses_repo.get_expenses_totals_in_range = AsyncMock(return_value=None)

    sample_movement = ShiftCashMovementInDb(
        id="mov-1",
        branchId="branch-1",
        shiftId="shift-1",
        docNumber="MOV-001",
        type="out",
        amount=15_000,
        reason="Compra de agua",
        registerAsExpense=False,
        createdBy=UserInfo(id="user-1", name="Cajero"),
        createdAt=1_700_000_000_000,
    )
    controller.shift_cash_movements_repo = MagicMock()
    controller.shift_cash_movements_repo.get_all_shift_cash_movements = AsyncMock(
        return_value=[sample_movement]
    )

    params = TotalsFilterParams(
        branchId="branch-1",
        startDate=1_700_000_000_000,
        endDate=1_700_086_400_000,
        userId="user-1",
    )
    result = await controller.get_total_results_by_date_range(params)

    assert len(result.shiftCashMovements) == 1
    assert result.shiftCashMovements[0].id == "mov-1"
    called_params: ShiftCashMovementFilterParams = (
        controller.shift_cash_movements_repo.get_all_shift_cash_movements.call_args.args[
            0
        ]
    )
    assert called_params.branchId == "branch-1"
    assert called_params.createdBy == "user-1"
    assert called_params.startDate == 1_700_000_000_000
    assert called_params.endDate == 1_700_086_400_000
