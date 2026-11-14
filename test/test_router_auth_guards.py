import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.tools import BranchesTool, EtagTool
from kardex.tools.users_tool import UsersTool


@pytest.fixture(autouse=True)
def _skip_tenant_caches(monkeypatch):
    """Evita tocar MongoDB: el guard de auth corre antes del endpoint."""

    async def _noop(self, nickname: str | None = None) -> None:
        return None

    monkeypatch.setattr(BranchesTool, "ensure_loaded", _noop)
    monkeypatch.setattr(UsersTool, "ensure_loaded", _noop)
    monkeypatch.setattr(EtagTool, "ensure_loaded", _noop)


@pytest.fixture(scope="module")
def client() -> TestClient:
    import main

    return TestClient(main.app)


BUSINESS_ROUTES = [
    "/api/v1/app-settings",
    "/api/v1/products",
    "/api/v1/product-categories",
    "/api/v1/product-prices",
    "/api/v1/product-accounts/products/p1/accounts",
    "/api/v1/product-transactions",
    "/api/v1/product-stats",
    "/api/v1/expenses",
    "/api/v1/expense-categories",
    "/api/v1/integrations",
    "/api/v1/reports/general-report",
    "/api/v1/user-roles",
    "/api/v1/daily-summaries",
]


@pytest.mark.parametrize("path", BUSINESS_ROUTES)
def test_business_routes_require_token(client: TestClient, path: str):
    response = client.get(path, headers={"X-Servin": "tienda-a"})

    assert response.status_code == 401, path


def test_export_route_requires_token(client: TestClient):
    response = client.get(
        "/api/v1/exports/price-list",
        headers={"X-Servin": "tienda-a", "X-Branch": "ORIGIN_BRANCH"},
    )

    assert response.status_code == 401


def test_tenant_header_is_checked_before_auth(client: TestClient):
    response = client.get("/api/v1/products")

    assert response.status_code == 400
    assert "tenant header" in response.json()["detail"]
