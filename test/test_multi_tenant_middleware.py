import sys
from pathlib import Path

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app_middleware.depends import multi_tenant_middleware
from kardex.kardex_config import kardexCtx
from kardex.tools import BranchesTool, EtagTool
from kardex.tools.users_tool import UsersTool


@pytest.fixture(autouse=True)
def _skip_tenant_caches(monkeypatch):
    """Evita tocar MongoDB: el middleware solo se prueba en su capa HTTP."""

    async def _noop(self, nickname: str | None = None) -> None:
        return None

    monkeypatch.setattr(BranchesTool, "ensure_loaded", _noop)
    monkeypatch.setattr(UsersTool, "ensure_loaded", _noop)
    monkeypatch.setattr(EtagTool, "ensure_loaded", _noop)


def _make_client() -> TestClient:
    app = FastAPI()
    api = APIRouter(dependencies=[Depends(multi_tenant_middleware)])

    @api.get("/whoami")
    async def whoami() -> dict[str, str]:
        ctx = kardexCtx.get()
        return {"tenant": ctx.businessNickname, "branch": ctx.branchId}

    app.include_router(api, prefix="/api/v1")
    return TestClient(app)


def test_missing_tenant_header_returns_400():
    client = _make_client()

    response = client.get("/api/v1/whoami")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Missing required tenant header ('X-Servin' or 'x-tenant-nickname')"
    )


def test_invalid_nickname_returns_400():
    client = _make_client()

    response = client.get("/api/v1/whoami", headers={"X-Servin": "AB"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid tenant nickname"


def test_reserved_nickname_returns_400():
    client = _make_client()

    response = client.get("/api/v1/whoami", headers={"X-Servin": "admin"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid tenant nickname"


def test_valid_header_sets_context():
    client = _make_client()

    response = client.get(
        "/api/v1/whoami",
        headers={"X-Servin": "tienda-a", "X-Branch": "ORIGIN_BRANCH"},
    )

    assert response.status_code == 200
    assert response.json() == {"tenant": "tienda-a", "branch": "ORIGIN_BRANCH"}


def test_nickname_is_normalized_and_alias_header_is_accepted():
    client = _make_client()

    response = client.get(
        "/api/v1/whoami", headers={"x-tenant-nickname": "  TiendaA  "}
    )

    assert response.status_code == 200
    assert response.json()["tenant"] == "tiendaa"


@pytest.mark.asyncio
async def test_middleware_loads_the_three_synchronous_caches(monkeypatch):
    calls: list[str] = []

    def recorder(name: str):
        async def _ensure(self, nickname: str | None = None) -> None:
            calls.append(name)

        return _ensure

    monkeypatch.setattr(BranchesTool, "ensure_loaded", recorder("branches"))
    monkeypatch.setattr(UsersTool, "ensure_loaded", recorder("users"))
    monkeypatch.setattr(EtagTool, "ensure_loaded", recorder("etag"))

    client = _make_client()
    response = client.get("/api/v1/whoami", headers={"X-Servin": "tienda-a"})

    assert response.status_code == 200
    assert sorted(calls) == ["branches", "etag", "users"]


def test_context_does_not_leak_between_requests():
    client = _make_client()

    first = client.get("/api/v1/whoami", headers={"X-Servin": "tienda-a"})
    second = client.get("/api/v1/whoami", headers={"X-Servin": "tienda-b"})

    assert first.json()["tenant"] == "tienda-a"
    assert second.json()["tenant"] == "tienda-b"
    # Fuera de un request no queda contexto publicado en este task.
    assert kardexCtx.get().businessNickname == ""
