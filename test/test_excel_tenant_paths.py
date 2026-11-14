import sys
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

import services.excel_service as excel_service
from kardex.kardex_config import KardexContext, kardexCtx
from kardex.tools import InvalidTenantNickname, TenantContextMissingError
from services.excel_service import ProjectionExcelService, PriceListService


def _set_tenant(nickname: str):
    return kardexCtx.set(KardexContext(businessNickname=nickname))


def test_excel_paths_are_isolated_per_tenant(monkeypatch, tmp_path):
    monkeypatch.setattr(excel_service, "STATIC_PATH", tmp_path)

    token = _set_tenant("tienda-a")
    try:
        projection_a = ProjectionExcelService().get_projection_xslx()
        price_list_a = PriceListService().get_price_list_xslx()
    finally:
        kardexCtx.reset(token)

    token = _set_tenant("tienda-b")
    try:
        projection_b = ProjectionExcelService().get_projection_xslx()
        price_list_b = PriceListService().get_price_list_xslx()
    finally:
        kardexCtx.reset(token)

    assert projection_a == tmp_path / "tienda-a" / "projection.xlsx"
    assert price_list_a == tmp_path / "tienda-a" / "price_list.xlsx"
    assert projection_a != projection_b
    assert price_list_a != price_list_b
    assert projection_b.parent.name == "tienda-b"


def test_excel_path_requires_tenant(monkeypatch, tmp_path):
    monkeypatch.setattr(excel_service, "STATIC_PATH", tmp_path)

    with pytest.raises(TenantContextMissingError):
        excel_service.get_tenant_static_path()


def test_excel_path_normalizes_nickname(monkeypatch, tmp_path):
    monkeypatch.setattr(excel_service, "STATIC_PATH", tmp_path)

    token = _set_tenant("TiendaA")
    try:
        path = excel_service.get_tenant_static_path()
    finally:
        kardexCtx.reset(token)

    assert path.name == "tiendaa"


@pytest.mark.parametrize(
    "nickname", ["../../escape", "..", "admin", "config", "a"]
)
def test_excel_path_rejects_invalid_or_reserved_nicknames(
    monkeypatch, tmp_path, nickname: str
):
    monkeypatch.setattr(excel_service, "STATIC_PATH", tmp_path)

    with pytest.raises(InvalidTenantNickname):
        excel_service.get_tenant_static_path(nickname)


def test_excel_path_never_escapes_static_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(excel_service, "STATIC_PATH", tmp_path)

    path = excel_service.get_tenant_static_path("tienda-a")

    assert path.is_relative_to(tmp_path.resolve())
