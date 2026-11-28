from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kardex.core.invoice_cancellation_register import (
    approve_cancellation_request,
    cancel_cancellation_request,
    create_cancellation_request,
    reject_cancellation_request,
    validate_invoice_cancellable,
)
from kardex.core.role_manager.role_manager import CommercialSubModules, RoleManager
from kardex.core.shift_register.shift_totals import (
    PaymentBreakdown,
    compute_shift_totals,
)
from kardex.repos.v1.common.models import ClientInfo, ProductItem, SaleItem, UserInfo
from kardex.repos.v1.invoice_cancellation_requests import (
    CreateInvoiceCancellationRequest,
)
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.services.mongo_collections.v1.invoices_collection import InvoicesCollection
from kardex.tools import InvalidOperation


def _user(user_id: str = "u-1", name: str = "Cajero") -> UserInfo:
    return UserInfo(id=user_id, name=name)


def _client_info() -> ClientInfo:
    return ClientInfo(name="Cliente General", phone="", address="")


def _sale_item(
    product_id: str = "p-1",
    quantity: int = 2,
    bon_quantity: int = 1,
    cost: int = 500,
    price: int = 1000,
) -> SaleItem:
    return SaleItem(
        product=ProductItem(
            id=product_id,
            name="Producto Test",
            productType="item",
            code="P001",
            unitName="Unidad",
        ),
        quantity=quantity,
        bonQuantity=bon_quantity,
        cost=cost,
        price=price,
        subTotal=quantity * price,
        total=quantity * price,
    )


def _invoice_dict(
    *,
    invoice_id: str = "inv-1",
    doc_number: str = "F-0001",
    payment_type: str = "cash",
    status: str = "paid",
    amount_paid: int = 2000,
    total: int = 2000,
    shift_id: str | None = None,
) -> dict:
    return {
        "id": invoice_id,
        "branchId": "b-1",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "docNumber": doc_number,
        "saleItems": [_sale_item().model_dump()],
        "amountPaid": amount_paid,
        "status": status,
        "paymentType": payment_type,
        "totalCost": 1500,
        "total": total,
        "createdBy": _user().model_dump(),
        "shiftId": shift_id,
        "createdAt": 1700000000000,
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


@pytest.mark.asyncio
async def test_create_cancellation_request_success():
    inv = _invoice_dict()
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=inv)

    requests_col = MagicMock()
    requests_col.fetch_pending_by_invoice_id = AsyncMock(return_value=None)
    requests_col.create_request = AsyncMock(return_value=None)

    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])

    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    counter_mgr = MagicMock()
    counter_mgr.next_invoice_cancellation_request_number = AsyncMock(
        return_value="0001"
    )

    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.CounterManager",
            return_value=counter_mgr,
        ),
    ):
        result = await create_cancellation_request(
            CreateInvoiceCancellationRequest(
                invoiceId="inv-1",
                reason="Error en cobro",
                requestedBy=_user(),
            )
        )

    assert result.status == "pending"
    assert result.docNumber == "0001"
    assert result.invoiceDocNumber == "F-0001"
    requests_col.create_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_cancellation_request_allows_closed_shift_when_setting_enabled():
    inv = _invoice_dict(shift_id="shift-closed")
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=inv)

    requests_col = MagicMock()
    requests_col.fetch_pending_by_invoice_id = AsyncMock(return_value=None)
    requests_col.create_request = AsyncMock(return_value=None)

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )

    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])

    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    counter_mgr = MagicMock()
    counter_mgr.next_invoice_cancellation_request_number = AsyncMock(
        return_value="0001"
    )

    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.CounterManager",
            return_value=counter_mgr,
        ),
    ):
        result = await create_cancellation_request(
            CreateInvoiceCancellationRequest(
                invoiceId="inv-1",
                reason="Error en cobro",
                requestedBy=_user(),
            )
        )

    assert result.status == "pending"
    assert result.invoiceDocNumber == "F-0001"
    requests_col.create_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_rejects_credit_invoice_with_payments_or_closed_shift():
    credit_paid = _invoice_dict(
        payment_type="credit", status="partiallyPaid", amount_paid=500
    )
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=credit_paid)
    requests_col = MagicMock()

    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
    ):
        with pytest.raises(InvalidOperation, match="abonos"):
            await create_cancellation_request(
                CreateInvoiceCancellationRequest(
                    invoiceId="inv-1",
                    reason="Cliente canceló",
                    requestedBy=_user(),
                )
            )

    closed_shift_inv = _invoice_dict(shift_id="shift-1")
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=closed_shift_inv)
    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(return_value={"id": "shift-1", "status": "closed"})

    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
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
            await create_cancellation_request(
                CreateInvoiceCancellationRequest(
                    invoiceId="inv-1",
                    reason="Error en factura",
                    requestedBy=_user(),
                )
            )

    draft_inv = _invoice_dict(status="draft")
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=draft_inv)
    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
    ):
        with pytest.raises(InvalidOperation, match="borrador"):
            await create_cancellation_request(
                CreateInvoiceCancellationRequest(
                    invoiceId="inv-1",
                    reason="Error",
                    requestedBy=_user(),
                )
            )

    applied_dev_inv = _invoice_dict()
    invoices_col.fetch_invoice_by_id = AsyncMock(return_value=applied_dev_inv)
    dev_col = MagicMock()
    dev_col.fetch_devolutions_by_invoice_id = AsyncMock(
        return_value=[{"id": "dev-1", "status": "applied"}]
    )
    with (
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.create_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=dev_col,
        ),
    ):
        with pytest.raises(InvalidOperation, match="devoluciones"):
            await create_cancellation_request(
                CreateInvoiceCancellationRequest(
                    invoiceId="inv-1",
                    reason="Error",
                    requestedBy=_user(),
                )
            )


@pytest.mark.asyncio
async def test_validate_invoice_cancellable_allows_closed_shift_when_setting_enabled():
    invoice = InvoiceInDb.model_validate(_invoice_dict(shift_id="shift-1"))

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-1", "status": "closed"}
    )
    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        await validate_invoice_cancellable(invoice)


@pytest.mark.asyncio
async def test_validate_invoice_cancellable_blocks_active_devolutions_when_setting_enabled():
    invoice = InvoiceInDb.model_validate(_invoice_dict(shift_id="shift-1"))

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-1", "status": "closed"}
    )
    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(
        return_value=[{"id": "dev-1", "status": "applied"}]
    )
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        with pytest.raises(InvalidOperation, match="devoluciones"):
            await validate_invoice_cancellable(invoice)


@pytest.mark.asyncio
async def test_validate_invoice_cancellable_treats_shift_without_status_as_closed():
    invoice = InvoiceInDb.model_validate(_invoice_dict(shift_id="shift-1"))
    session = object()

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(return_value={"id": "shift-1"})
    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
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
            await validate_invoice_cancellable(invoice, session=session)

    shift_call = shifts_col.fetch_shift_by_id.await_args
    assert shift_call is not None
    assert shift_call.kwargs["session"] is session
    devolutions_col.fetch_devolutions_by_invoice_id.assert_not_awaited()
    credit_notes_col.fetch_credit_notes_by_invoice_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_invoice_cancellable_propagates_session_to_queries():
    invoice = InvoiceInDb.model_validate(_invoice_dict())
    session = object()

    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
    ):
        await validate_invoice_cancellable(invoice, session=session)

    devolutions_call = devolutions_col.fetch_devolutions_by_invoice_id.await_args
    assert devolutions_call is not None
    assert devolutions_call.kwargs == {
        "invoice_id": "inv-1",
        "client_id": None,
        "session": session,
    }
    credit_notes_call = credit_notes_col.fetch_credit_notes_by_invoice_id.await_args
    assert credit_notes_call is not None
    assert credit_notes_call.kwargs == {
        "invoice_id": "inv-1",
        "session": session,
    }


@pytest.mark.asyncio
async def test_approve_cash_invoice_returns_stock_and_marks_cancelled():
    inv = _invoice_dict(shift_id="shift-open")
    req_doc = {
        "id": "req-1",
        "docNumber": "0001",
        "branchId": "b-1",
        "invoiceId": "inv-1",
        "invoiceDocNumber": "F-0001",
        "invoiceTotal": 2000,
        "invoicePaymentType": "cash",
        "invoiceStatus": "paid",
        "invoiceShiftId": "shift-open",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error de digitación",
        "requestedBy": _user().model_dump(),
        "status": "approved",
        "createdAt": 1700000000000,
        "reviewedBy": _user("sup-1", "Supervisor").model_dump(),
        "reviewedAt": 1700000005000,
    }

    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=req_doc)

    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(return_value=inv)
    invoices_col.update_invoice_by_id_with_session = AsyncMock(return_value=inv)

    prd_account_col = MagicMock()
    prd_account_col.update_product_account_balance_data = AsyncMock(
        return_value={
            "id": "pa-1",
            "productId": "p-1",
            "branchId": "b-1",
            "currentStock": 13,
            "promiseStock": 0,
            "averageCost": 500,
            "lastCost": 500,
            "createdAt": 1700000000000,
        }
    )

    prd_tx_col = MagicMock()
    prd_tx_col.create_many_product_transactions_with_session = AsyncMock(
        return_value=None
    )

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-open", "status": "open"}
    )
    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.MongoService",
            return_value=SimpleNamespace(client=_mock_mongo_client()),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductAccountsCollection.get_instance",
            return_value=prd_account_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductTransactionsCollection.get_instance",
            return_value=prd_tx_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientTransactionsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.fetch_product_types_map",
            AsyncMock(return_value={"p-1": "item"}),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
    ):
        res = await approve_cancellation_request(
            request_id="req-1",
            reviewed_by=_user("sup-1", "Supervisor"),
            review_notes="Aprobado",
        )

    assert res.status == "approved"
    # quantity (2) + bonQuantity (1) = 3 reingresados
    prd_account_col.update_product_account_balance_data.assert_awaited_once()
    call_kwargs = prd_account_col.update_product_account_balance_data.call_args.kwargs
    assert call_kwargs["add_to_current_stock"] == 3
    tx_payload = (
        prd_tx_col.create_many_product_transactions_with_session.call_args.args[0][0]
    )
    assert tx_payload["subtype"] == "invoice_cancellation"
    assert tx_payload["type"] == "entry"
    invoices_col.update_invoice_by_id_with_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_cash_invoice_closed_shift_when_setting_enabled():
    inv = _invoice_dict(shift_id="shift-closed")
    req_doc = {
        "id": "req-1",
        "docNumber": "0001",
        "branchId": "b-1",
        "invoiceId": "inv-1",
        "invoiceDocNumber": "F-0001",
        "invoiceTotal": 2000,
        "invoicePaymentType": "cash",
        "invoiceStatus": "paid",
        "invoiceShiftId": "shift-closed",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error de digitación",
        "requestedBy": _user().model_dump(),
        "status": "approved",
        "createdAt": 1700000000000,
        "reviewedBy": _user("sup-1", "Supervisor").model_dump(),
        "reviewedAt": 1700000005000,
    }

    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=req_doc)

    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(return_value=inv)
    invoices_col.update_invoice_by_id_with_session = AsyncMock(return_value=inv)

    prd_account_col = MagicMock()
    prd_account_col.update_product_account_balance_data = AsyncMock(
        return_value={
            "id": "pa-1",
            "productId": "p-1",
            "branchId": "b-1",
            "currentStock": 13,
            "promiseStock": 0,
            "averageCost": 500,
            "lastCost": 500,
            "createdAt": 1700000000000,
        }
    )

    prd_tx_col = MagicMock()
    prd_tx_col.create_many_product_transactions_with_session = AsyncMock(
        return_value=None
    )

    shifts_col = MagicMock()
    shifts_col.fetch_shift_by_id = AsyncMock(
        return_value={"id": "shift-closed", "status": "closed"}
    )
    devolutions_col = MagicMock()
    devolutions_col.fetch_devolutions_by_invoice_id = AsyncMock(return_value=[])
    credit_notes_col = MagicMock()
    credit_notes_col.fetch_credit_notes_by_invoice_id = AsyncMock(return_value=[])

    with (
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.MongoService",
            return_value=SimpleNamespace(client=_mock_mongo_client()),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductAccountsCollection.get_instance",
            return_value=prd_account_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductTransactionsCollection.get_instance",
            return_value=prd_tx_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientTransactionsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.fetch_product_types_map",
            AsyncMock(return_value={"p-1": "item"}),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.ShiftsCollection.get_instance",
            return_value=shifts_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=devolutions_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=credit_notes_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.AppSettingsTool",
            return_value=SimpleNamespace(
                get_current_app_settings=AsyncMock(
                    return_value=SimpleNamespace(
                        allowCancellationsOutsideShift=True
                    )
                )
            ),
        ),
    ):
        res = await approve_cancellation_request(
            request_id="req-1",
            reviewed_by=_user("sup-1", "Supervisor"),
            review_notes="Aprobado fuera de turno",
        )

    assert res.status == "approved"
    prd_account_col.update_product_account_balance_data.assert_awaited_once()
    call_kwargs = prd_account_col.update_product_account_balance_data.call_args.kwargs
    assert call_kwargs["add_to_current_stock"] == 3
    invoices_col.update_invoice_by_id_with_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_credit_invoice_without_payments_reverses_client_balance():
    inv = _invoice_dict(payment_type="credit", status="open", amount_paid=0, total=3500)
    req_doc = {
        "id": "req-2",
        "docNumber": "0002",
        "branchId": "b-1",
        "invoiceId": "inv-1",
        "invoiceDocNumber": "F-0001",
        "invoiceTotal": 3500,
        "invoicePaymentType": "credit",
        "invoiceStatus": "open",
        "clientId": "c-1",
        "clientInfo": _client_info().model_dump(),
        "reason": "Error de crédito",
        "requestedBy": _user().model_dump(),
        "status": "approved",
        "createdAt": 1700000000000,
    }

    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(return_value=req_doc)
    invoices_col = MagicMock()
    invoices_col.fetch_invoice_by_id_with_session = AsyncMock(return_value=inv)
    invoices_col.update_invoice_by_id_with_session = AsyncMock(return_value=inv)
    prd_account_col = MagicMock()
    prd_account_col.update_product_account_balance_data = AsyncMock(
        return_value={
            "id": "pa-1",
            "productId": "p-1",
            "branchId": "b-1",
            "currentStock": 10,
            "promiseStock": 0,
            "averageCost": 500,
            "lastCost": 500,
            "createdAt": 1700000000000,
        }
    )
    prd_tx_col = MagicMock()
    prd_tx_col.create_many_product_transactions_with_session = AsyncMock(
        return_value=None
    )
    finance_mock = AsyncMock(return_value=None)

    with (
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.MongoService",
            return_value=SimpleNamespace(client=_mock_mongo_client()),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
            return_value=requests_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.InvoicesCollection.get_instance",
            return_value=invoices_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductAccountsCollection.get_instance",
            return_value=prd_account_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ProductTransactionsCollection.get_instance",
            return_value=prd_tx_col,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientTransactionsCollection.get_instance",
            return_value=MagicMock(),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.fetch_product_types_map",
            AsyncMock(return_value={"p-1": "item"}),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.approve_cancellation_request.ClientFinanceEngine.process_movement",
            finance_mock,
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.DevolutionsCollection.get_instance",
            return_value=MagicMock(fetch_devolutions_by_invoice_id=AsyncMock(return_value=[])),
        ),
        patch(
            "kardex.core.invoice_cancellation_register.validate_invoice_cancellable.CreditNotesCollection.get_instance",
            return_value=MagicMock(fetch_credit_notes_by_invoice_id=AsyncMock(return_value=[])),
        ),
    ):
        await approve_cancellation_request(
            request_id="req-2",
            reviewed_by=_user("sup-1", "Supervisor"),
        )

    finance_mock.assert_awaited_once()
    req_arg = finance_mock.call_args.kwargs["request"]
    assert req_arg.amount == -3500
    assert req_arg.subtype == "invoice_cancellation"


@pytest.mark.asyncio
async def test_reject_and_cancel_request_transitions():
    requests_col = MagicMock()
    requests_col.transition_request_status = AsyncMock(
        return_value={
            "id": "req-1",
            "docNumber": "0001",
            "branchId": "b-1",
            "invoiceId": "inv-1",
            "invoiceDocNumber": "F-0001",
            "invoiceTotal": 1000,
            "invoicePaymentType": "cash",
            "invoiceStatus": "paid",
            "clientId": "c-1",
            "clientInfo": _client_info().model_dump(),
            "reason": "Error",
            "requestedBy": _user().model_dump(),
            "status": "rejected",
            "createdAt": 1700000000000,
            "reviewNotes": "No procede",
        }
    )

    with patch(
        "kardex.core.invoice_cancellation_register.reject_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
        return_value=requests_col,
    ):
        rejected = await reject_cancellation_request(
            "req-1", _user("sup-1", "Supervisor"), "No procede"
        )
    assert rejected.status == "rejected"

    requests_col.transition_request_status = AsyncMock(
        return_value={
            **rejected.model_dump(),
            "status": "cancelled",
        }
    )
    with patch(
        "kardex.core.invoice_cancellation_register.cancel_cancellation_request.InvoiceCancellationRequestsCollection.get_instance",
        return_value=requests_col,
    ):
        cancelled = await cancel_cancellation_request("req-1", _user())
    assert cancelled.status == "cancelled"


def test_shift_totals_includes_cancelled_invoices_without_double_subtraction():
    totals = compute_shift_totals(
        initial_cash=1000,
        invoices=PaymentBreakdown(cash=5000, count=2),
        cancelled_invoices=PaymentBreakdown(cash=1500, credit=500, count=2),
    )
    assert totals.expectedCash == 6000
    assert totals.grandTotal == 5000
    assert totals.cancelledInvoiceCashTotal == 1500
    assert totals.cancelledInvoiceCreditTotal == 500
    assert totals.cancelledInvoiceCashSalesTotal == 1500
    assert totals.cancelledInvoiceTotal == 2000
    assert totals.cancelledInvoiceCount == 2


def test_role_manager_assigns_approve_cancellation_only_to_supervisor():
    roles = {r.name: r for r in RoleManager.get_default_roles()}
    assert (
        CommercialSubModules.APPROVE_INVOICE_CANCELLATION
        in roles["Supervisor"].access
    )
    assert (
        CommercialSubModules.APPROVE_INVOICE_CANCELLATION
        not in roles["Cajero"].access
    )
    assert (
        CommercialSubModules.APPROVE_INVOICE_CANCELLATION
        not in roles["Operador"].access
    )


@pytest.mark.asyncio
async def test_fetch_pending_to_paid_invoices_excludes_cancelled():
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=[])
    cursor.close = AsyncMock(return_value=None)

    mongo_col = MagicMock()
    mongo_col.find = MagicMock(return_value=cursor)

    col = InvoicesCollection.__new__(InvoicesCollection)
    col._collection = mongo_col

    await col.fetch_pending_to_paid_invoices("c-1")
    query_arg = mongo_col.find.call_args.args[0]
    assert query_arg["status"] == {"$in": ["open", "partiallyPaid"]}
