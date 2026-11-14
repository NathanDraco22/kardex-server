from io import BytesIO
import pytest
from fastapi import UploadFile

from app.api.v1.imports.imports_controller import imports_controller


def _create_upload_file(content: str, filename: str = "test.csv") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content.encode("utf-8")))


@pytest.mark.asyncio
async def test_preview_inventory_valid():
    csv_content = (
        "name,brandName,unitName,quantity,cost,price\n"
        "Aceite 1L,Mobil,Unidad,10,50.00,75.00\n"
        "Filtro Aire,Fram,Pieza,5,20.50,30.00\n"
    )
    upload = _create_upload_file(csv_content)
    result = await imports_controller.preview_import(
        import_type="inventory",
        branch_id="fake-branch",
        file=upload,
    )

    assert result.importType == "inventory"
    assert result.totalRows == 2
    assert result.totalQuantity == 15
    # 10 * 5000 + 5 * 2050 = 50000 + 10250 = 60250 cents
    assert result.totalCost == 60250
    # 10 * 7500 + 5 * 3000 = 75000 + 15000 = 90000 cents
    assert result.totalPrice == 90000


@pytest.mark.asyncio
async def test_preview_clients_valid():
    csv_content = (
        "name,cardId,phone,address,location,email,group,creditLimit,initialBalance\n"
        "Juan Perez,1234,555-0001,Calle 1,Centro,juan@mail.com,Minoristas,500.00,150.00\n"
        "Maria Lopez,,555-0002,,,,Mayoristas,1000.00,0\n"
    )
    upload = _create_upload_file(csv_content)
    result = await imports_controller.preview_import(
        import_type="clients",
        branch_id="fake-branch",
        file=upload,
    )

    assert result.importType == "clients"
    assert result.totalRows == 2
    assert result.totalCreditLimit == 150000  # 1500.00 * 100
    assert result.totalInitialBalance == 15000  # 150.00 * 100


@pytest.mark.asyncio
async def test_preview_suppliers_valid():
    csv_content = (
        "name,cardId,email,phone\n"
        "Distribuidora El Sol,12345,sol@example.com,555-1234\n"
        "Lubricantes del Norte,,lube@example.com,\n"
    )
    upload = _create_upload_file(csv_content)
    result = await imports_controller.preview_import(
        import_type="suppliers",
        branch_id=None,
        file=upload,
    )

    assert result.isValid is True
    assert result.importType == "suppliers"
    assert result.totalRows == 2
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_preview_inventory_with_errors():
    csv_content = (
        "name,brandName,unitName,quantity,cost,price\n"
        "Aceite 1L,,Unidad,10,not_a_cost,75.00\n"
        ",Fram,Pieza,invalid_qty,20.00,30.00\n"
    )
    upload = _create_upload_file(csv_content)
    result = await imports_controller.preview_import(
        import_type="inventory",
        branch_id=None,
        file=upload,
    )

    assert result.isValid is False
    assert result.totalRows == 2
    assert len(result.errors) > 0
