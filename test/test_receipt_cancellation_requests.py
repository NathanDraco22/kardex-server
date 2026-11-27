from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kardex.core.receipt_cancellation_register import (
    approve_receipt_cancellation_request,
    cancel_receipt_cancellation_request,
    create_receipt_cancellation_request,
    reject_receipt_cancellation_request,
    validate_receipt_cancellable,
)
from kardex.core.role_manager.role_manager import CommercialSubModules, RoleManager
from kardex.core.shift_register.shift_totals import (
    PaymentBreakdown,
    compute_shift_totals,
)
from kardex.repos.v1.app_settings.models.app_setting_model import (
    BaseAppSetting,
    UpdateAppSetting,
)
from kardex.repos.v1.common.models import ClientInfo, UserInfo
from kardex.repos.v1.receipt_cancellation_requests import (
    CreateReceiptCancellationRequest,
)
from kardex.repos.v1.receipts import ReceiptInDb
from kardex.tools import InvalidOperation


def _user(user_id: str = "u-1", name: str = "Cajero") -> UserInfo:
    return UserInfo(id=user_id, name=name)


def _client_info() -> ClientInfo:
    return ClientInfo(name="Cliente Crédito", phone="", address="")


def _receipt_dict(
    *,
    receipt_id: str = "rec-1",
    doc_number: str = "R-0001",
    total: int = 1500,
    is_deleted: bool = False,
    shift_id: str | None = None,
) -> dict:
    return {
        "id": receipt_id,
        "branchId": "b-1",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "docNumber": doc_number,
        "appliedInvoices": [
            {"invoiceId": "inv-1", "docNumber": "F-0001", "amountApplied": total}
        ],
        "appliedDevolutions": [],
        "appliedCreditNotes": [],
        "paymentMethod": "cash",
        "bankReference": "",
        "total": total,
        "createdBy": _user().model_dump(),
        "shiftId": shift_id,
        "createdAt": 1700000000000,
        "isDeleted": is_deleted,
    }


def _mock_mongo_client() -> MagicMock:
    tx_ctx = MagicMock()
    tx_ctx.__aenter__ = AsyncMock(return_value=None)
    tx_ctx.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.start_transaction = AsyncMock(return_value=tx_ctx)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session)
    session_ctx.__aexit__ = AsyncMock(return_value=None)

    client = MagicMock()
    client.start_session = MagicMock(return_value=session_ctx)
    return client


def test_app_settings_cancellation_flags_default_false():
    settings = BaseAppSetting()
    assert settings.useInvoiceCancellations is False
    assert settings.useReceiptCancellations is False
    assert settings.allowCancellationsOutsideShift is False

    upd_receipt = UpdateAppSetting(useReceiptCancellations=True)
    assert upd_receipt.model_dump(exclude_unset=True) == {
        "useReceiptCancellations": True
    }

    upd_outside = UpdateAppSetting(allowCancellationsOutsideShift=True)
    assert upd_outside.model_dump(exclude_unset=True) == {
        "allowCancellationsOutsideShift": True
    }


def test_role_manager_assigns_approve_receipt_cancellation_to_supervisor():
    roles = {r.name: r for r in RoleManager.get_default_roles()}
    assert (
        CommercialSubModules.APPROVE_RECEIPT_CANCELLATION
        in roles["Supervisor"].access
    )
    assert (
        CommercialSubModules.APPROVE_RECEIPT_CANCELLATION
        not in roles["Cajero"].access
    )


@pytest.mark.asyncio
async def test_create_receipt_cancellation_request_allows_paid_invoice():
    rec = _receipt_dict()
    receipts_col = MagicMock()
    receipts_col.fetch_receipt_by_id = AsyncMock(return_value=rec)

    requests_col = MagicMock()
    requests_col.fetch_pending_by_receipt_id = AsyncMock(return_value=None)
    requests_col.create_request = AsyncMock(return_value=None)

    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(
        return_value={"id": "inv-1", "status": "paid"}
    )

    counter_mgr = MagicMock()
    counter_mgr.next_receipt_cancellation_request_number = AsyncMock(
        return_value="0001"
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.CounterManager",
            return_value=counter_mgr,
        ),
    ):
        res = await create_receipt_cancellation_request(
            CreateReceiptCancellationRequest(
                receiptId="rec-1",
                reason="Monto errado",
                requestedBy=_user(),
            )
        )

    assert res.status == "pending"
    assert res.docNumber == "0001"
    assert res.receiptDocNumber == "R-0001"


@pytest.mark.asyncio
async def test_rejects_deleted_receipt_or_closed_shift():
    deleted_rec = _receipt_dict(is_deleted=True)
    receipts_col = MagicMock()
    receipts_col.fetch_receipt_by_id = AsyncMock(return_value=deleted_rec)

    with (
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=MagicMock(),
        ),
    ):
        with pytest.raises(InvalidOperation, match="ya se encuentra anulado"):
            await create_receipt_cancellation_request(
                CreateReceiptCancellationRequest(
                    receiptId="rec-1",
                    reason="Duplicado",
                    requestedBy=_user(),
                )
            )

    closed_rec = _receipt_dict(shift_id="shift-closed")
    receipts_col.fetch_receipt_by_id = AsyncMock(return_value=closed_rec)
    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=False
                    )
                )
            ),
        ),
    ):
        with pytest.raises(InvalidOperation, match="turno ya cerrado"):
            await create_receipt_cancellation_request(
                CreateReceiptCancellationRequest(
                    receiptId="rec-1",
                    reason="Error",
                    requestedBy=_user(),
                )
            )

    dev_rec = _receipt_dict()
    dev_rec["appliedDevolutions"] = [
        {"devolutionId": "dev-1", "docNumber": "D-0001", "amountApplied": 200}
    ]
    receipts_col.fetch_receipt_by_id = AsyncMock(return_value=dev_rec)
    with (
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.create_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=MagicMock(),
        ),
    ):
        with pytest.raises(InvalidOperation, match="devoluciones o notas de crédito"):
            await create_receipt_cancellation_request(
                CreateReceiptCancellationRequest(
                    receiptId="rec-1",
                    reason="Error",
                    requestedBy=_user(),
                )
            )


@pytest.mark.asyncio
async def test_validate_receipt_cancellable_allows_closed_shift_when_setting_enabled():
    receipt = ReceiptInDb.model_validate(_receipt_dict(shift_id="shift-closed"))

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(
        return_value={"id": "inv-1", "status": "paid"}
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        await validate_receipt_cancellable(receipt)


@pytest.mark.asyncio
async def test_validate_receipt_cancellable_blocks_cancelled_invoice_when_setting_enabled():
    receipt = ReceiptInDb.model_validate(_receipt_dict(shift_id="shift-closed"))

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(
        return_value={"id": "inv-1", "status": "cancelled"}
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        with pytest.raises(InvalidOperation, match="no permite revertir"):
            await validate_receipt_cancellable(receipt)


@pytest.mark.asyncio
async def test_approve_receipt_cancellation_reverses_paid_invoice_and_balance():
    rec = _receipt_dict(total=1500, shift_id="shift-open")
    req_doc = {
        "id": "rreq-1",
        "docNumber": "0001",
        "branchId": "b-1",
        "receiptId": "rec-1",
        "receiptDocNumber": "R-0001",
        "receiptTotal": 1500,
        "receiptPaymentMethod": "cash",
        "receiptShiftId": "shift-open",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error en abono",
        "requestedBy": _user().model_dump(),
        "status": "approved",
        "createdAt": 1700000000000,
    }

    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=req_doc)

    receipts_col = MagicMock()
    receipts_col.get_receipt_by_id_with_session = AsyncMock(return_value=rec)
    receipts_col.mark_receipt_cancelled_with_session = AsyncMock(return_value=rec)

    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(
        return_value={"id": "inv-1", "status": "paid"}
    )
    invoices_col.subtract_from_amount_paid = AsyncMock(return_value=None)

    clients_col = MagicMock()
    clients_col.add_to_client_balance = AsyncMock(
        return_value={
            "id": "c-1",
            "name": "Cliente Crédito",
            "phone": "",
            "address": "",
            "balance": 1500,
            "creditLimit": 10000,
            "createdAt": 1700000000000,
        }
    )

    client_tx_col = MagicMock()
    client_tx_col.create_client_transaction_with_session = AsyncMock(return_value=None)

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-open", "status": "open"}
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.MongoService",
            return_value=SimpleNamespace(client=_mock_mongo_client()),
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ClientsCollection.get_instance",
            return_value=clients_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ClientTransactionsCollection.get_instance",
            return_value=client_tx_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
    ):
        res = await approve_receipt_cancellation_request(
            request_id="rreq-1",
            reviewed_by=_user("sup-1", "Supervisor"),
            review_notes="Aprobado",
        )

    assert res.status == "approved"
    invoices_col.subtract_from_amount_paid.assert_awaited_once()
    clients_col.add_to_client_balance.assert_awaited_once()
    client_tx_col.create_client_transaction_with_session.assert_awaited_once()
    receipts_col.mark_receipt_cancelled_with_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_receipt_cancellation_closed_shift_when_setting_enabled():
    rec = _receipt_dict(total=1500, shift_id="shift-closed")
    req_doc = {
        "id": "rreq-1",
        "docNumber": "0001",
        "branchId": "b-1",
        "receiptId": "rec-1",
        "receiptDocNumber": "R-0001",
        "receiptTotal": 1500,
        "receiptPaymentMethod": "cash",
        "receiptShiftId": "shift-closed",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error en abono",
        "requestedBy": _user().model_dump(),
        "status": "approved",
        "createdAt": 1700000000000,
    }

    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=req_doc)

    receipts_col = MagicMock()
    receipts_col.get_receipt_by_id_with_session = AsyncMock(return_value=rec)
    receipts_col.mark_receipt_cancelled_with_session = AsyncMock(return_value=rec)

    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(
        return_value={"id": "inv-1", "status": "paid"}
    )
    invoices_col.subtract_from_amount_paid = AsyncMock(return_value=None)

    clients_col = MagicMock()
    clients_col.add_to_client_balance = AsyncMock(
        return_value={
            "id": "c-1",
            "name": "Cliente Crédito",
            "phone": "",
            "address": "",
            "balance": 1500,
            "creditLimit": 10000,
            "createdAt": 1700000000000,
        }
    )

    client_tx_col = MagicMock()
    client_tx_col.create_client_transaction_with_session = AsyncMock(return_value=None)

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )

    with (
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.MongoService",
            return_value=SimpleNamespace(client=_mock_mongo_client()),
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ReceiptsCollection.get_instance",
            return_value=receipts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ClientsCollection.get_instance",
            return_value=clients_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.approve_cancellation_request.ClientTransactionsCollection.get_instance",
            return_value=client_tx_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.receipt_cancellation_register.validate_receipt_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        res = await approve_receipt_cancellation_request(
            request_id="rreq-1",
            reviewed_by=_user("sup-1", "Supervisor"),
            review_notes="Aprobado fuera de turno",
        )

    assert res.status == "approved"
    invoices_col.subtract_from_amount_paid.assert_awaited_once()
    clients_col.add_to_client_balance.assert_awaited_once()
    client_tx_col.create_client_transaction_with_session.assert_awaited_once()
    receipts_col.mark_receipt_cancelled_with_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_and_cancel_receipt_request():
    base_doc = {
        "id": "rreq-1",
        "docNumber": "0001",
        "branchId": "b-1",
        "receiptId": "rec-1",
        "receiptDocNumber": "R-0001",
        "receiptTotal": 1000,
        "receiptPaymentMethod": "cash",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error",
        "requestedBy": _user().model_dump(),
        "status": "rejected",
        "createdAt": 1700000000000,
        "reviewNotes": "No aplica",
    }
    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=base_doc)

    with patch(
        "kardex.core.receipt_cancellation_register.reject_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
        return_value=requests_col,
    ):
        rejected = await reject_receipt_cancellation_request(
            "rreq-1", _user("sup-1", "Supervisor"), "No aplica"
        )
    assert rejected.status == "rejected"

    requests_col.transition_request_status = AsyncMock(
        return_value={**base_doc, "status": "cancelled"}
    )
    with patch(
        "kardex.core.receipt_cancellation_register.cancel_cancellation_request.ReceiptCancellationRequestsCollection.get_instance",
        return_value=requests_col,
    ):
        cancelled = await cancel_receipt_cancellation_request("rreq-1", _user())
    assert cancelled.status == "cancelled"


def test_shift_totals_includes_cancelled_receipts_without_double_subtraction():
    from kardex.core.shift_register.shift_totals import is_document_counted

    totals = compute_shift_totals(
        initial_cash=1000,
        receipts=PaymentBreakdown(cash=2500, count=1),
        cancelled_receipt_total=1500,
        cancelled_receipt_count=1,
    )
    assert totals.expectedCash == 3500
    assert totals.grandTotal == 2500
    assert totals.cancelledReceiptTotal == 1500
    assert totals.cancelledReceiptCount == 1
    assert is_document_counted("receipts", "cancelled") is False
    assert is_document_counted("receipts", None) is True
