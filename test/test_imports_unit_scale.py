import io
import pytest
from fastapi import HTTPException, UploadFile

from api.v1.imports.imports_controller import ImportsController
from kardex.repos.v1.products.models.product_model import ExtraUnit
from kardex.repos.v1.unit_scales import UnitScaleInDb
from kardex.services.mongo_collections.v1 import UnitScalesCollection
from kardex.tools import BranchesTool


def _sample_scales() -> list[dict]:
    libra_decimal = UnitScaleInDb(
        id="scale-libra-dec",
        name="Libra (Decimal)",
        scaleType="weight",
        baseUnit="0.01 Libra",
        units=[
            ExtraUnit(name="Libra", conversionFactor=100),
            ExtraUnit(name="Arroba (25 lb)", conversionFactor=2500),
            ExtraUnit(name="Quintal (100 lb)", conversionFactor=10000),
        ],
        defaultUnitIndex=1,
        wholesaleUnitIndex=3,
        priceUnitFactor=100,
        createdAt=1000,
    )
    libra_quarter = UnitScaleInDb(
        id="scale-libra-q",
        name="Libra",
        scaleType="weight",
        baseUnit="1/4 Libra",
        units=[
            ExtraUnit(name="Libra", conversionFactor=4),
            ExtraUnit(name="Arroba (25 lb)", conversionFactor=100),
        ],
        defaultUnitIndex=1,
        wholesaleUnitIndex=2,
        priceUnitFactor=1,
        createdAt=1000,
    )
    return [libra_decimal.model_dump(), libra_quarter.model_dump()]


def _make_csv_upload(content: str) -> UploadFile:
    return UploadFile(
        filename="inventario.csv",
        file=io.BytesIO(content.encode("utf-8")),
    )


def _patch_scales_and_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeUnitScalesCol:
        async def fetch_all_unit_scales(self) -> list[dict]:
            return _sample_scales()

    monkeypatch.setattr(
        UnitScalesCollection,
        "get_instance",
        classmethod(lambda cls: FakeUnitScalesCol()),
    )
    monkeypatch.setattr(
        BranchesTool,
        "get_branch_by_id",
        lambda self, branch_id: {"id": branch_id, "name": "Central"},
    )


@pytest.mark.asyncio
async def test_import_resolves_libra_decimal_by_name_and_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_scales_and_branch(monkeypatch)
    controller = ImportsController()
    lookup = await controller._load_unit_scales_lookup(["name", "unitScale"])

    # Resolución por nombre case-insensitive, unitName vacío, cantidad decimal 12.5
    p1 = controller._build_single_product_import(
        {
            "__row_number__": "2",
            "name": "Lomo de Res",
            "brandName": "Carnicería",
            "unitName": "",
            "unitScale": "libra (decimal)",
            "quantity": "12.5",
            "cost": "14.50",
            "price": "18.50",
        },
        lookup,
    )
    assert p1.unitName == "0.01 Libra"
    assert p1.priceUnitFactor == 100
    assert p1.defaultUnitIndex == 1
    assert len(p1.extraUnits) == 3
    assert p1.quantity == 1250
    assert p1.cost == 1450
    assert p1.price == 1850

    # Resolución por ID exacto
    p2 = controller._build_single_product_import(
        {
            "__row_number__": "3",
            "name": "Costilla",
            "brandName": "Carnicería",
            "unitScale": "scale-libra-dec",
            "quantity": "1.35",
            "cost": "10.00",
            "price": "15.25",
        },
        lookup,
    )
    assert p2.unitName == "0.01 Libra"
    assert p2.priceUnitFactor == 100
    assert p2.quantity == 135
    assert p2.cost == 1000
    assert p2.price == 1525


@pytest.mark.asyncio
async def test_import_quarter_scale_converts_cost_and_rejects_invalid_multiple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_scales_and_branch(monkeypatch)
    controller = ImportsController()
    lookup = await controller._load_unit_scales_lookup(["name", "unitScale"])

    # 1.25 lb en escala de cuartos -> 5 cuartos, precio 20.00/lb -> 500¢ por cuarto
    p = controller._build_single_product_import(
        {
            "__row_number__": "2",
            "name": "Queso",
            "brandName": "Lácteos",
            "unitScale": "Libra",
            "quantity": "1.25",
            "cost": "16.00",
            "price": "20.00",
        },
        lookup,
    )
    assert p.unitName == "1/4 Libra"
    assert p.priceUnitFactor == 1
    assert p.quantity == 5
    assert p.cost == 400
    assert p.price == 500

    # 1.3 lb no es múltiplo de 0.25 -> error 400
    with pytest.raises(HTTPException) as exc_info:
        controller._build_single_product_import(
            {
                "__row_number__": "3",
                "name": "Queso",
                "brandName": "Lácteos",
                "unitScale": "Libra",
                "quantity": "1.3",
                "cost": "16.00",
                "price": "20.00",
            },
            lookup,
        )
    assert exc_info.value.status_code == 400
    assert "múltiplo válido" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_import_rejects_unknown_scale_and_keeps_legacy_rows_working(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_scales_and_branch(monkeypatch)
    controller = ImportsController()
    lookup = await controller._load_unit_scales_lookup(["name", "unitScale"])

    # Fila sin unitScale -> funciona idéntico a antes
    legacy = controller._build_single_product_import(
        {
            "__row_number__": "2",
            "name": "Refresco",
            "brandName": "Marca",
            "unitName": "Unidad",
            "unitScale": "",
            "quantity": "10",
            "cost": "12.00",
            "price": "15.00",
        },
        lookup,
    )
    assert legacy.unitName == "Unidad"
    assert legacy.priceUnitFactor == 1
    assert legacy.extraUnits == []
    assert legacy.quantity == 10
    assert legacy.cost == 1200
    assert legacy.price == 1500

    # Escala inexistente -> error 400
    with pytest.raises(HTTPException) as exc_info:
        controller._build_single_product_import(
            {
                "__row_number__": "3",
                "name": "Carne",
                "brandName": "Marca",
                "unitScale": "Escala Inventada",
                "quantity": "5",
                "cost": "10.00",
                "price": "15.00",
            },
            lookup,
        )
    assert exc_info.value.status_code == 400
    assert "no corresponde a ninguna escala" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_preview_import_calculates_exact_totals_with_price_unit_factor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_scales_and_branch(monkeypatch)
    controller = ImportsController()

    csv_content = (
        "name,brandName,unitName,unitScale,quantity,cost,price\n"
        "Lomo de Res,Carnicería,,Libra (Decimal),12.5,14.50,18.50\n"
        "Bolsa,Genérica,Unidad,,10,2.00,3.00\n"
    )
    preview = await controller.preview_import(
        import_type="inventory",
        branch_id="b1",
        file=_make_csv_upload(csv_content),
    )
    assert preview.isValid is True
    assert preview.totalRows == 2
    # 12.5 lb × 14.50 = 181.25 (18125¢) + 10 × 2.00 = 20.00 (2000¢) -> 20125¢
    assert preview.totalCost == 20125
    # 12.5 lb × 18.50 = 231.25 (23125¢) + 10 × 3.00 = 30.00 (3000¢) -> 26125¢
    assert preview.totalPrice == 26125
