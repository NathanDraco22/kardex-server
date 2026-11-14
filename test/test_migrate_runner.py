import sys
from pathlib import Path
from typing import Any, cast

import pytest
from pymongo.errors import PyMongoError

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.core.tenant import migrate_tenants
from kardex.services import MongoService


class _FakeClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _restore_mongo_client():
    """Evita que el cliente falso quede en el singleton para otras pruebas."""

    service = MongoService()
    had_client = hasattr(service, "client")
    previous = getattr(service, "client", None)

    yield

    if had_client:
        service.client = cast(Any, previous)
    elif hasattr(service, "client"):
        del service.client


@pytest.mark.asyncio
async def test_run_initializes_mongo_service_before_using_collections(monkeypatch):
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

    assert exit_code == 0
    assert calls["init_client"] is True
    assert calls["client"] is MongoService().client
    assert fake_client.closed is True


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
