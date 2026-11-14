import sys
from pathlib import Path
from typing import Any, cast

import pytest
from pymongo.errors import OperationFailure, PyMongoError

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.core.tenant import migrate_tenants
from kardex.core.tenant.migrate_tenants import (
    AdoptTenantError,
    validate_adoptable_nickname,
)
from kardex.services import MongoService, mongo_indexes
from kardex.services.mongo_collections.v1 import MetaCollection
from kardex.tools import TenantIndexBuildError


class _FakeClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _restore_mongo_client():
    """Cada prueba arranca sin cliente y restaura el estado anterior."""

    service = MongoService()
    had_client = hasattr(service, "client")
    previous = getattr(service, "client", None)

    if had_client:
        del service.client

    yield

    if had_client:
        service.client = cast(Any, previous)
    elif hasattr(service, "client"):
        del service.client


@pytest.mark.asyncio
async def test_run_creates_and_closes_its_own_client(monkeypatch):
    calls: dict = {}
    fake_client = _FakeClient()

    async def fake_init_client(self) -> None:
        calls["init_client"] = True
        self.client = fake_client

    async def fake_list_databases(client, only=None):
        calls["client"] = client
        return []

    monkeypatch.setattr(MongoService, "init_client", fake_init_client)
    monkeypatch.setattr(
        migrate_tenants, "list_tenant_databases", fake_list_databases
    )

    exit_code = await migrate_tenants.run(
        migrate_tenants.parse_args(["--indexes", "--dry-run"])
    )

    service = MongoService()

    assert exit_code == 0
    assert calls["init_client"] is True
    assert calls["client"] is fake_client
    assert fake_client.closed is True
    # El runner no deja un cliente cerrado colgado en el singleton.
    assert hasattr(service, "client") is False


@pytest.mark.asyncio
async def test_run_reuses_existing_client_and_does_not_close_it(monkeypatch):
    service = MongoService()
    previous_client = _FakeClient()
    service.client = cast(Any, previous_client)
    calls: dict = {"init_client": False}

    async def fake_init_client(self) -> None:
        calls["init_client"] = True
        self.client = _FakeClient()

    async def fake_list_databases(client, only=None):
        calls["client"] = client
        return []

    monkeypatch.setattr(MongoService, "init_client", fake_init_client)
    monkeypatch.setattr(
        migrate_tenants, "list_tenant_databases", fake_list_databases
    )

    exit_code = await migrate_tenants.run(
        migrate_tenants.parse_args(["--indexes", "--dry-run"])
    )

    assert exit_code == 0
    assert calls["init_client"] is False
    assert calls["client"] is previous_client
    assert previous_client.closed is False
    assert service.client is previous_client


@pytest.mark.asyncio
async def test_run_reports_cluster_errors_without_traceback(monkeypatch, capsys):
    async def fake_init_client(self) -> None:
        self.client = _FakeClient()

    async def fake_list_databases(client, only=None):
        raise PyMongoError("sin conexion")

    monkeypatch.setattr(MongoService, "init_client", fake_init_client)
    monkeypatch.setattr(
        migrate_tenants, "list_tenant_databases", fake_list_databases
    )

    exit_code = await migrate_tenants.run(
        migrate_tenants.parse_args(["--indexes", "--dry-run"])
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "ERROR" in captured.err
    assert "sin conexion" in captured.err


@pytest.mark.asyncio
async def test_run_reports_adopt_errors(monkeypatch):
    async def fake_init_client(self) -> None:
        self.client = _FakeClient()

    async def fake_list_databases(client, only=None):
        return []

    async def fake_list_adoptable(client, only=None):
        raise PyMongoError("sin conexion")

    monkeypatch.setattr(MongoService, "init_client", fake_init_client)
    monkeypatch.setattr(
        migrate_tenants, "list_tenant_databases", fake_list_databases
    )
    monkeypatch.setattr(
        migrate_tenants, "list_adoptable_databases", fake_list_adoptable
    )

    exit_code = await migrate_tenants.run(
        migrate_tenants.parse_args(["--adopt", "--dry-run"])
    )

    assert exit_code == 1


def test_validate_adoptable_nickname_accepts_normalized():
    assert validate_adoptable_nickname("tienda-a") == "tienda-a"


@pytest.mark.parametrize(
    "nickname",
    ["admin", "config", "local", "kardexcontrol", "AB", "../escape", " tienda "],
)
def test_validate_adoptable_nickname_rejects_invalid_or_reserved(nickname: str):
    with pytest.raises(AdoptTenantError):
        validate_adoptable_nickname(nickname)


def test_validate_adoptable_nickname_rejects_uppercase_database_name():
    with pytest.raises(AdoptTenantError) as exc:
        validate_adoptable_nickname("TiendaLegacy")

    assert "mongorestore" in str(exc.value)


def test_current_index_version_covers_core_settings_index():
    assert mongo_indexes.CURRENT_INDEX_VERSION == 2


@pytest.mark.asyncio
async def test_ensure_indexes_reports_index_build_errors(monkeypatch, capsys):
    async def fake_read_meta(self) -> dict:
        return {"isProvisioned": True, "indexesVersion": 1}

    async def fake_create_indexes(nickname: str) -> None:
        raise OperationFailure("E11000 duplicate key error")

    monkeypatch.setattr(MetaCollection, "read_tenant_meta", fake_read_meta)
    monkeypatch.setattr(
        mongo_indexes, "create_tenant_indexes", fake_create_indexes
    )

    with pytest.raises(TenantIndexBuildError) as exc:
        await mongo_indexes.ensure_indexes_for_tenant("tienda-a")

    assert exc.value.nickname == "tienda-a"
    assert "CoreSettings" in str(exc.value)
    assert capsys.readouterr().err == ""
