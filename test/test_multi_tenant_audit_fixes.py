import importlib
from typing import Any

import pytest
from fastapi import HTTPException, Response

from app_middleware.depends.cache_header_response import (
    cache_header_response_midnight,
)
from api.v1.app_settings.app_settings_controller import app_settings_controller
from kardex.kardex_config import KardexContext, kardexCtx
from kardex.repos.v1.app_settings import (
    AppSettingInDb,
    AppSettingsDataSource,
    AppSettingsRepository,
)
from kardex.repos.v1.branches import BranchInDb, BranchesRepository
from kardex.repos.v1.integrations import IntegrationInDb, IntegrationsRepository
from kardex.repos.v1.users import UserInDb, UsersRepository
from kardex.services.mongo_collections.v1 import BranchesCollection, UsersCollection
from kardex.tools import BranchesTool, EtagTool
from kardex.tools.app_settings_tool import AppSettingsTool
from kardex.tools.integration_tool import IntegrationTool
from kardex.tools.tenant_cache import BoundedTenantCache
from kardex.tools.users_tool import UsersTool

provision_module = importlib.import_module("kardex.core.tenant.provision_tenant")


def _set_tenant(nickname: str):
    return kardexCtx.set(KardexContext(businessNickname=nickname))


@pytest.mark.asyncio
async def test_get_current_app_settings_does_not_upsert_missing_tenant():
    class _EmptyAppSettingsDS(AppSettingsDataSource):
        def __init__(self) -> None:
            self.upserts = 0

        async def get_app_setting_by_id(self, app_setting_id: str):
            return None

        async def get_all_app_settings(self):
            return []

        async def create_app_setting_if_absent(self, app_setting: dict[str, Any]):
            self.upserts += 1

    ds = _EmptyAppSettingsDS()
    repo = AppSettingsRepository(app_settings_ds=ds)

    result = await repo.get_current_app_settings()

    assert result is None
    assert ds.upserts == 0


@pytest.mark.asyncio
async def test_app_settings_controller_returns_404_and_does_not_cache_none(
    monkeypatch,
):
    async def _return_none(self):
        return None

    monkeypatch.setattr(
        AppSettingsRepository, "get_current_app_settings", _return_none
    )

    token = _set_tenant("ghost-tenant")
    try:
        with pytest.raises(HTTPException) as exc_info:
            await app_settings_controller.get_current_app_settings()
    finally:
        kardexCtx.reset(token)

    assert exc_info.value.status_code == 404
    cache = getattr(AppSettingsTool, "_AppSettingsTool__current_app_settings")
    assert "ghost-tenant" not in cache


@pytest.mark.asyncio
async def test_cache_header_response_uses_private_and_tenant_vary():
    response = Response()
    response.headers["Vary"] = "Accept-Encoding"

    await cache_header_response_midnight(response)

    cache_control = response.headers["Cache-Control"]
    assert cache_control.startswith("private, max-age=")
    assert "public" not in cache_control

    vary_headers = [h.strip().lower() for h in response.headers["Vary"].split(",")]
    assert "accept-encoding" in vary_headers
    assert "x-servin" in vary_headers
    assert "x-tenant-nickname" in vary_headers
    assert "authorization" in vary_headers


def test_bounded_tenant_cache_evicts_lru():
    cache: BoundedTenantCache[str] = BoundedTenantCache(maxsize=2)
    cache["tenant-a"] = "A"
    cache["tenant-b"] = "B"

    # Acceder a tenant-a lo vuelve el mas reciente; tenant-b debe salir primero.
    assert cache.get("tenant-a") == "A"
    cache["tenant-c"] = "C"

    assert list(cache.keys()) == ["tenant-a", "tenant-c"]
    assert "tenant-b" not in cache


@pytest.mark.asyncio
async def test_etag_update_branches_does_not_grow_collection_instances(monkeypatch):
    class _FakeCollection:
        async def estimated_document_count(self) -> int:
            return 4

    observed_tenants: list[str] = []

    def _fake_prop(self):
        observed_tenants.append(kardexCtx.get().businessNickname)
        return _FakeCollection()

    BranchesCollection._instances.clear()
    monkeypatch.setattr(BranchesCollection, "_collection", property(_fake_prop))

    token = _set_tenant("tienda-a")
    try:
        await EtagTool().update_branches_etags("tienda-b")
    finally:
        kardexCtx.reset(token)

    assert observed_tenants == ["tienda-b"]
    assert BranchesCollection._instances == {}
    etag = EtagTool().get_etag("branches_count", nickname="tienda-b")
    assert etag is not None and etag.value == "4"


@pytest.mark.asyncio
async def test_cache_tools_isolate_explicit_nickname_from_active_context(monkeypatch):
    async def _fake_branches(self):
        tenant = kardexCtx.get().businessNickname
        return [BranchInDb(id="b1", name=f"branch-{tenant}", createdAt=0)]

    async def _fake_inactive_users(self):
        tenant = kardexCtx.get().businessNickname
        return [
            UserInDb(
                id="u1",
                username=f"user-{tenant}",
                password="x",
                role="Admin",
                isActive=False,
                createdAt=0,
            )
        ]

    async def _fake_app_settings(self):
        tenant = kardexCtx.get().businessNickname
        return AppSettingInDb(
            id="Default",
            companyLogoUrl=f"https://{tenant}.local/logo.png",
            createdAt=0,
        )

    async def _fake_integrations(self):
        tenant = kardexCtx.get().businessNickname
        return [IntegrationInDb(id=f"int-{tenant}", createdAt=0)]

    monkeypatch.setattr(BranchesRepository, "get_all_branches", _fake_branches)
    monkeypatch.setattr(
        UsersRepository, "get_all_inactive_users", _fake_inactive_users
    )
    monkeypatch.setattr(
        AppSettingsRepository, "get_current_app_settings", _fake_app_settings
    )
    monkeypatch.setattr(
        IntegrationsRepository, "get_all_integrations", _fake_integrations
    )

    token = _set_tenant("tienda-a")
    try:
        await BranchesTool().refresh_current_branches("tienda-b")
        await UsersTool().refresh_inactive_users("tienda-b")
        await AppSettingsTool().refresh_current_app_settings("tienda-b")
        await IntegrationTool().refresh_current_integration("tienda-b")

        # El contexto activo sigue siendo tienda-a.
        assert kardexCtx.get().businessNickname == "tienda-a"
    finally:
        kardexCtx.reset(token)

    token_b = _set_tenant("tienda-b")
    try:
        branch = BranchesTool().get_branch_by_id("b1")
        user = UsersTool().get_inactive_user_by_id("u1")
        app_setting = await AppSettingsTool().get_current_app_settings()
        integration = await IntegrationTool().get_current_integration()
    finally:
        kardexCtx.reset(token_b)

    assert branch is not None and branch.name == "branch-tienda-b"
    assert user is not None and user.username == "user-tienda-b"
    assert (
        app_setting is not None
        and app_setting.companyLogoUrl == "https://tienda-b.local/logo.png"
    )
    assert integration.id == "int-tienda-b"


@pytest.mark.asyncio
async def test_provision_tenant_creates_users_indexes_before_owner_when_deferred(
    monkeypatch,
):
    order: list[str] = []

    async def _noop(*args, **kwargs):
        return None

    async def _record_users_indexes(self):
        order.append("users_indexes")

    async def _record_root():
        order.append("root_user")

    async def _record_owner(owner_name: str):
        order.append(f"owner:{owner_name}")

    monkeypatch.setattr(provision_module, "create_default_client", _noop)
    monkeypatch.setattr(provision_module, "create_default_branch", _noop)
    monkeypatch.setattr(provision_module, "create_default_roles", _noop)
    monkeypatch.setattr(UsersCollection, "create_indexes", _record_users_indexes)
    monkeypatch.setattr(provision_module, "create_root_user", _record_root)
    monkeypatch.setattr(provision_module, "_create_owner_if_absent", _record_owner)
    monkeypatch.setattr(provision_module, "create_default_expense_categories", _noop)
    monkeypatch.setattr(provision_module, "create_default_unit_scales", _noop)
    monkeypatch.setattr(provision_module, "create_default_app_settings", _noop)
    monkeypatch.setattr(provision_module, "create_default_integration", _noop)
    monkeypatch.setattr(provision_module, "write_tenant_meta_document", _noop)
    monkeypatch.setattr(BranchesTool, "refresh_current_branches", _noop)
    monkeypatch.setattr(EtagTool, "update_branches_etags", _noop)

    await provision_module.provision_tenant(
        "tienda-nueva",
        establishment_name="Tienda Nueva",
        owner_name="Ana",
        run_indexes=False,
    )

    assert order == ["users_indexes", "root_user", "owner:Ana"]
