import io
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from api.v1.imports.imports_controller import imports_controller
from kardex.core.imports.accounts_payable.model.account_payable_import import (
    AccountPayableImport,
)
from kardex.core.imports.accounts_payable.process_accounts_payable_import import (
    process_accounts_payable_import,
)


def _csv_upload(content: str, filename: str = "cuentas_por_pagar.csv") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content.encode("utf-8")))


@pytest.mark.asyncio
async def test_preview_accounts_payable_valid_calculates_totals_and_new_suppliers():
    csv_text = (
        "supplierName,docNumber,date,expirationDate,amount,amountPaid,description\n"
        "Distribuidora Norte,FAC-101,2026-11-01,2026-12-01,100.00,25.00,Compra 1\n"
        "Proveedor Existente,FAC-102,05/11/2026,,50.50,0,Compra 2\n"
        "Distribuidora Norte,,2026-11-10,2026-11-20,30.00,30.00,Pagada\n"
    )

    mock_expenses_col = MagicMock()
    mock_expenses_col.fetch_existing_doc_numbers = AsyncMock(return_value=set())

    mock_suppliers_col = MagicMock()
    mock_suppliers_col.fetch_all_suppliers = AsyncMock(
        return_value=[
            {
                "id": "0001",
                "name": "Proveedor Existente",
                "creditDays": 15,
                "isActive": True,
                "isDeleted": False,
                "createdAt": 1_700_000_000_000,
            }
        ]
    )

    with (
        patch.object(imports_controller, "_validate_branch", return_value=None),
        patch(
            "api.v1.imports.imports_controller.ExpensesCollection.get_instance",
            return_value=mock_expenses_col,
        ),
        patch(
            "api.v1.imports.imports_controller.SuppliersCollection.get_instance",
            return_value=mock_suppliers_col,
        ),
    ):
        preview = await imports_controller.preview_import(
            "accountsPayable", "branch-1", _csv_upload(csv_text)
        )

    assert preview.isValid is True
    assert preview.importType == "accountsPayable"
    assert preview.totalRows == 3
    assert preview.totalPayableAmount == 180_50
    assert preview.totalPayablePaid == 55_00
    assert preview.totalPayablePending == 125_50
    assert preview.newSuppliersCount == 1
    assert preview.errors == []


@pytest.mark.asyncio
async def test_preview_accounts_payable_detects_validation_and_duplicate_errors():
    csv_text = (
        "supplierName,docNumber,date,expirationDate,amount,amountPaid,description\n"
        "Proveedor A,ERR-1,2026-11-01,,100.00,150.00,Sobrepago\n"
        "Proveedor B,ERR-2,fecha-mala,,0,0,Monto cero\n"
        "Proveedor C,DUP-1,2026-11-01,,40.00,0,Ok 1\n"
        "Proveedor D,DUP-1,2026-11-01,,45.00,0,Duplicado CSV\n"
        "Proveedor E,EXIST-9,2026-11-01,,80.00,0,Ya existe en BD\n"
    )

    mock_expenses_col = MagicMock()
    mock_expenses_col.fetch_existing_doc_numbers = AsyncMock(return_value={"EXIST-9"})

    mock_suppliers_col = MagicMock()
    mock_suppliers_col.fetch_all_suppliers = AsyncMock(return_value=[])

    with (
        patch.object(imports_controller, "_validate_branch", return_value=None),
        patch(
            "api.v1.imports.imports_controller.ExpensesCollection.get_instance",
            return_value=mock_expenses_col,
        ),
        patch(
            "api.v1.imports.imports_controller.SuppliersCollection.get_instance",
            return_value=mock_suppliers_col,
        ),
    ):
        preview = await imports_controller.preview_import(
            "accountsPayable", "branch-1", _csv_upload(csv_text)
        )

    assert preview.isValid is False
    messages = "\n".join(err.message for err in preview.errors)
    assert "amountPaid" in messages
    assert "amount" in messages
    assert "DUP-1" in messages
    assert "EXIST-9" in messages


@pytest.mark.asyncio
async def test_process_accounts_payable_import_creates_suppliers_and_expenses():
    items = [
        AccountPayableImport(
            supplierName="proveedor existente",
            docNumber=None,
            date=1_700_000_000_000,
            expirationDate=None,
            amount=100_00,
            amountPaid=40_00,
            description="Factura parcial",
        ),
        AccountPayableImport(
            supplierName="Nuevo Proveedor S.A.",
            docNumber="FAC-555",
            date=1_700_000_000_000,
            expirationDate=1_700_500_000_000,
            amount=50_00,
            amountPaid=50_00,
            description="Factura pagada",
        ),
    ]

    created_suppliers: list[dict] = []
    created_expenses: list[dict] = []

    mock_suppliers_col = MagicMock()
    mock_suppliers_col.fetch_all_suppliers = AsyncMock(
        return_value=[
            {
                "id": "0001",
                "name": "Proveedor Existente",
                "creditDays": 10,
                "isActive": True,
                "isDeleted": False,
                "createdAt": 1_700_000_000_000,
            }
        ]
    )
    mock_suppliers_col.create_many_suppliers_with_session = AsyncMock(
        side_effect=lambda docs, session=None: created_suppliers.extend(docs)
    )

    mock_expenses_col = MagicMock()
    mock_expenses_col.fetch_existing_doc_numbers = AsyncMock(return_value=set())
    mock_expenses_col.create_many_expenses_with_session = AsyncMock(
        side_effect=lambda docs, session=None: created_expenses.extend(docs)
    )

    class _FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        @asynccontextmanager
        async def _tx(self):
            yield

        async def start_transaction(self):
            return self._tx()

    class _FakeMongoClient:
        def start_session(self):
            return _FakeSession()

    mock_mongo_service = MagicMock()
    mock_mongo_service.client = _FakeMongoClient()

    mock_counter = MagicMock()
    mock_counter.next_supplier_number = AsyncMock(return_value="0002")
    mock_counter.set_supplier_number = AsyncMock(return_value="0002")
    mock_counter.next_expense_number = AsyncMock(return_value="0010")
    mock_counter.set_expense_number = AsyncMock(return_value="0010")

    with (
        patch(
            "kardex.core.imports.accounts_payable.process_accounts_payable_import.SuppliersCollection.get_instance",
            return_value=mock_suppliers_col,
        ),
        patch(
            "kardex.core.imports.accounts_payable.process_accounts_payable_import.ExpensesCollection.get_instance",
            return_value=mock_expenses_col,
        ),
        patch(
            "kardex.core.imports.accounts_payable.process_accounts_payable_import.MongoService",
            return_value=mock_mongo_service,
        ),
        patch(
            "kardex.core.imports.accounts_payable.process_accounts_payable_import.CounterManager",
            return_value=mock_counter,
        ),
    ):
        count = await process_accounts_payable_import("branch-1", items)

    assert count == 2
    assert len(created_suppliers) == 1
    assert created_suppliers[0]["name"] == "Nuevo Proveedor S.A."
    assert len(created_expenses) == 2

    first, second = created_expenses
    assert first["supplierId"] == "0001"
    assert first["docNumber"] == "0010"
    assert first["status"] == "partiallyPaid"
    assert first["expirationDate"] == 1_700_000_000_000 + 10 * 86_400_000
    assert len(first["payments"]) == 1
    assert first["payments"][0]["amount"] == 40_00

    assert second["supplierId"] == "0002"
    assert second["docNumber"] == "FAC-555"
    assert second["status"] == "paid"
    assert second["paidAt"] == 1_700_000_000_000
    assert second["createdAt"] == 1_700_000_000_000
    assert len(second["payments"]) == 1


def test_parse_optional_date_accepts_unix_timestamp_ms_and_seconds():
    assert (
        imports_controller._parse_optional_date("1732622400000", "date", "2")
        == 1_732_622_400_000
    )
    assert (
        imports_controller._parse_optional_date("1732622400", "date", "2")
        == 1_732_622_400_000
    )
