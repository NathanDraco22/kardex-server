from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kardex.repos.v1.common.filter_params import ExpensesFilterParams
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.expenses import (
    AccountsPayableSummary,
    AddToAmountRequest,
    CreateExpense,
    ExpensesRepository,
    UpdateExpense,
)
from kardex.services.mongo_collections.v1.expenses_collection import ExpensesCollection


def _make_expense_doc(
    *,
    expense_id: str = "exp-1",
    amount: int = 100_00,
    amount_paid: int = 0,
    status: str = "open",
    payments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": expense_id,
        "type": "supplier",
        "branchId": "branch-1",
        "docNumber": "FAC-001",
        "amount": amount,
        "category": "",
        "description": "Compra a crédito",
        "date": 1_700_000_000_000,
        "dateId": "2023-11-14",
        "amountPaid": amount_paid,
        "payments": payments or [],
        "supplierId": "sup-1",
        "supplierName": "Proveedor Uno",
        "status": status,
        "isActive": True,
        "expirationDate": 1_700_500_000_000,
        "createdBy": {"id": "u-1", "name": "Admin"},
        "paidAt": None,
        "shiftId": None,
        "isDeleted": False,
        "createdAt": 1_700_000_000_000,
        "updatedAt": None,
    }


@pytest.mark.asyncio
async def test_add_to_amount_paid_partial_and_final_liquidates_expense():
    ds = MagicMock()
    repo = ExpensesRepository(ds)

    open_doc = _make_expense_doc(amount=100_00, amount_paid=0, status="open")
    partial_doc = _make_expense_doc(amount=100_00, amount_paid=40_00, status="partiallyPaid")
    paid_doc = _make_expense_doc(amount=100_00, amount_paid=100_00, status="paid")

    ds.get_expense_by_id = AsyncMock(side_effect=[open_doc, partial_doc])

    recorded_payments: list[dict[str, Any]] = []

    async def fake_ds_add(
        expense_id: str, amount_paid: int, payment_record: dict[str, Any] | None = None
    ):
        assert expense_id == "exp-1"
        assert payment_record is not None
        recorded_payments.append(payment_record)
        if len(recorded_payments) == 1:
            return {**partial_doc, "payments": [payment_record]}
        return {**paid_doc, "paidAt": payment_record["paidAt"], "payments": list(recorded_payments)}

    ds.add_to_amount_paid = AsyncMock(side_effect=fake_ds_add)

    res1 = await repo.add_to_amount_paid(
        AddToAmountRequest(
            expenseId="exp-1",
            amountPaid=40_00,
            paymentMethod="transfer",
            reference="TRF-101",
            note="Primer abono",
            createdBy=UserInfo(id="u-1", name="Admin"),
        )
    )
    assert res1 is not None
    assert res1.status == "partiallyPaid"
    assert res1.amountPaid == 40_00
    assert len(res1.payments) == 1
    assert res1.payments[0].paymentMethod == "transfer"
    assert res1.payments[0].reference == "TRF-101"

    res2 = await repo.add_to_amount_paid(
        AddToAmountRequest(
            expenseId="exp-1",
            amountPaid=60_00,
            paymentMethod="cash",
            paidAt=1_700_100_000_000,
        )
    )
    assert res2 is not None
    assert res2.status == "paid"
    assert res2.amountPaid == 100_00
    assert res2.paidAt == 1_700_100_000_000
    assert len(res2.payments) == 2


@pytest.mark.asyncio
async def test_add_to_amount_paid_rejects_invalid_amounts_and_states():
    ds = MagicMock()
    repo = ExpensesRepository(ds)

    with pytest.raises(ValueError, match="mayor a cero"):
        await repo.add_to_amount_paid(AddToAmountRequest(expenseId="exp-1", amountPaid=0))

    ds.get_expense_by_id = AsyncMock(return_value=_make_expense_doc(amount=100_00, amount_paid=60_00, status="partiallyPaid"))
    with pytest.raises(ValueError, match="excede"):
        await repo.add_to_amount_paid(AddToAmountRequest(expenseId="exp-1", amountPaid=50_00))

    ds.get_expense_by_id = AsyncMock(return_value=_make_expense_doc(amount=100_00, amount_paid=100_00, status="paid"))
    with pytest.raises(ValueError, match="pagado o cancelado"):
        await repo.add_to_amount_paid(AddToAmountRequest(expenseId="exp-1", amountPaid=10_00))

    ds.get_expense_by_id = AsyncMock(return_value=_make_expense_doc(amount=100_00, amount_paid=0, status="cancelled"))
    with pytest.raises(ValueError, match="pagado o cancelado"):
        await repo.add_to_amount_paid(AddToAmountRequest(expenseId="exp-1", amountPaid=10_00))


@pytest.mark.asyncio
async def test_create_paid_expense_normalizes_amount_paid():
    ds = MagicMock()
    ds.create_expense = AsyncMock(side_effect=lambda doc, session=None: doc)
    repo = ExpensesRepository(ds)

    created = await repo.create_expense(
        CreateExpense(
            type="operative",
            branchId="branch-1",
            docNumber="G-001",
            amount=55_00,
            category="Servicios",
            date=1_700_000_000_000,
            dateId="2023-11-14",
            status="paid",
            createdBy=UserInfo(id="u-1", name="Admin"),
        )
    )

    assert created.amountPaid == 55_00
    assert created.paidAt is not None


def test_expenses_filter_params_only_pending():
    params = ExpensesFilterParams(offset=0, onlyPending=True)
    query = params.to_query_params()
    assert query["status"] == {"$in": ["draft", "open", "partiallyPaid"]}
    assert "onlyPending" not in query


@pytest.mark.asyncio
async def test_get_accounts_payable_summary_aggregates_by_supplier():
    col = ExpensesCollection.__new__(ExpensesCollection)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "_id": "sup-1",
                "supplierId": "sup-1",
                "supplierName": "Distribuidora Norte",
                "totalAmount": 200_00,
                "totalPaid": 50_00,
                "pendingAmount": 150_00,
                "overdueAmount": 100_00,
                "pendingCount": 2,
                "overdueCount": 1,
                "oldestDueDate": 1_700_000_000_000,
            },
            {
                "_id": "sup-2",
                "supplierId": "sup-2",
                "supplierName": "Importadora Sur",
                "totalAmount": 80_00,
                "totalPaid": 0,
                "pendingAmount": 80_00,
                "overdueAmount": 0,
                "pendingCount": 1,
                "overdueCount": 0,
                "oldestDueDate": 1_800_000_000_000,
            },
        ]
    )
    mock_cursor.close = AsyncMock()
    mock_collection = MagicMock()
    mock_collection.aggregate = AsyncMock(return_value=mock_cursor)
    col._collection = mock_collection

    ds = MagicMock()
    with patch.object(ExpensesCollection, "get_instance", return_value=col):
        raw_summary = await col.get_accounts_payable_summary(
            branch_id="branch-1", overdue_cutoff_ms=1_750_000_000_000
        )

    ds.get_accounts_payable_summary = AsyncMock(return_value=raw_summary)
    repo = ExpensesRepository(ds)
    summary = await repo.get_accounts_payable_summary(branch_id="branch-1")

    assert isinstance(summary, AccountsPayableSummary)
    assert summary.totalPending == 230_00
    assert summary.totalOverdue == 100_00
    assert summary.suppliersCount == 2
    assert summary.documentsCount == 3
    assert summary.suppliers[0].supplierName == "Distribuidora Norte"
    assert summary.suppliers[0].overdueCount == 1


@pytest.mark.asyncio
async def test_delete_expense_blocks_expenses_with_payments():
    ds = MagicMock()
    repo = ExpensesRepository(ds)

    ds.get_expense_by_id = AsyncMock(
        return_value=_make_expense_doc(
            amount=100_00,
            amount_paid=30_00,
            status="partiallyPaid",
            payments=[
                {
                    "id": "p-1",
                    "amount": 30_00,
                    "paymentMethod": "cash",
                    "paidAt": 1_700_000_000_000,
                    "createdAt": 1_700_000_000_000,
                }
            ],
        )
    )
    with pytest.raises(ValueError, match="abonos registrados"):
        await repo.delete_expense_by_id("exp-1")

    ds.get_expense_by_id = AsyncMock(return_value=_make_expense_doc(status="open"))
    ds.delete_expense_by_id = AsyncMock(return_value=_make_expense_doc(status="open"))
    deleted = await repo.delete_expense_by_id("exp-1")
    assert deleted is not None


@pytest.mark.asyncio
async def test_update_expense_validates_amount_and_status_with_payments():
    ds = MagicMock()
    repo = ExpensesRepository(ds)

    ds.get_expense_by_id = AsyncMock(
        return_value=_make_expense_doc(
            amount=100_00,
            amount_paid=60_00,
            status="partiallyPaid",
            payments=[
                {
                    "id": "p-1",
                    "amount": 60_00,
                    "paymentMethod": "cash",
                    "paidAt": 1_700_000_000_000,
                    "createdAt": 1_700_000_000_000,
                }
            ],
        )
    )
    with pytest.raises(ValueError, match="menor al total ya abonado"):
        await repo.update_expense_by_id("exp-1", UpdateExpense(amount=50_00))

    with pytest.raises(ValueError, match="abonos registrados"):
        await repo.update_expense_by_id("exp-1", UpdateExpense(status="open"))

    ds.update_expense_by_id = AsyncMock(
        return_value=_make_expense_doc(amount=120_00, amount_paid=120_00, status="paid")
    )
    await repo.update_expense_by_id(
        "exp-1", UpdateExpense(amount=120_00, status="paid")
    )
    sent_payload = ds.update_expense_by_id.call_args.args[1]
    assert sent_payload["amountPaid"] == 120_00
