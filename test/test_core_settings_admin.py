import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

import app.api.v1.core_settings.core_settings_controller as core_settings_module
from app.api.v1.core_settings.core_settings_controller import CoreSettingsController
from kardex.core.security import TokenManager
from kardex.kardex_config import KardexContext, kardexCtx
from kardex.repos.v1.core_settings import (
    CoreSettingInDb,
    CreateCoreSetting,
    DecodedCoreSetting,
    UpdateCoreSetting,
)
from kardex.services.mongo_collections.v1 import MetaCollection
from kardex.tools import normalize_nickname


# Forma real del header que envia service-manager-server en Authorization.
ID_TOKEN_PAYLOAD = {
    "sub": "servin-1",
    "origin": "Service Manager",
    "exp": 9999999999,
}

# Forma real del content_token que viaja en el body.
CONTENT_TOKEN_PAYLOAD = {
    "name": "Tienda A",
    "nickname": "tienda-a",
    "ownerName": "Propietario",
    "isMultiBranch": False,
    "isActive": True,
    "isUsingExpirationDate": True,
    "price": 0,
}


def _controller(repo: AsyncMock | None = None) -> CoreSettingsController:
    return CoreSettingsController(
        core_settings_repo=repo or AsyncMock(),
        branches_repo=AsyncMock(),
        users_repo=AsyncMock(),
    )


def _core_setting() -> CoreSettingInDb:
    return CoreSettingInDb(
        id="cs-1",
        nickname="tienda-a",
        token="content-token",
        createdAt=1700000000000,
    )


def _patch_token_manager(monkeypatch, decoded: dict | None) -> None:
    monkeypatch.setattr(
        TokenManager,
        "super_token_verify",
        staticmethod(lambda token: decoded),
    )


def test_patch_validates_path_against_content_token_nickname():
    controller = _controller()

    with pytest.raises(HTTPException) as exc:
        controller._assert_path_matches_token("tienda-b", CONTENT_TOKEN_PAYLOAD)

    assert exc.value.status_code == 403


def test_patch_normalizes_nicknames():
    controller = _controller()

    nickname = controller._assert_path_matches_token(
        "  TiendaA ", {"nickname": "tiendaa"}
    )

    assert nickname == "tiendaa"


def test_id_token_has_no_nickname():
    """El header de plataforma no sirve para resolver el tenant."""

    assert "nickname" not in ID_TOKEN_PAYLOAD

    with pytest.raises(HTTPException) as exc:
        CoreSettingsController._token_nickname(ID_TOKEN_PAYLOAD)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_patch_uses_content_token_not_header(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    repo = AsyncMock()
    repo.update_core_setting_by_nickname.return_value = _core_setting()
    controller = _controller(repo)

    result = await controller.update_core_setting_by_nickname(
        "tienda-a", UpdateCoreSetting(token="content-token")
    )

    assert result.nickname == "tienda-a"
    repo.update_core_setting_by_nickname.assert_awaited_once()
    called_nickname, _body = repo.update_core_setting_by_nickname.await_args.args
    assert called_nickname == "tienda-a"


@pytest.mark.asyncio
async def test_patch_without_content_token_returns_400(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    controller = _controller()

    with pytest.raises(HTTPException) as exc:
        await controller.update_core_setting_by_nickname(
            "tienda-a", UpdateCoreSetting()
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_patch_rejects_header_of_other_tenant(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    controller = _controller()
    token = kardexCtx.set(KardexContext(businessNickname="tienda-b"))
    try:
        with pytest.raises(HTTPException) as exc:
            await controller.update_core_setting_by_nickname(
                "tienda-a", UpdateCoreSetting(token="content-token")
            )
    finally:
        kardexCtx.reset(token)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_rejects_body_nickname_different_from_token(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    controller = _controller()
    body = CreateCoreSetting(nickname="tienda-b", token="super-token")

    with pytest.raises(HTTPException) as exc:
        await controller.create_core_setting(body)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_rejects_invalid_nickname(monkeypatch):
    _patch_token_manager(monkeypatch, {**CONTENT_TOKEN_PAYLOAD, "nickname": "admin"})
    controller = _controller()
    body = CreateCoreSetting(nickname="admin", token="super-token")

    with pytest.raises(HTTPException) as exc:
        await controller.create_core_setting(body)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_is_idempotent_when_tenant_is_provisioned(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    state = {"provisioned": False}

    async def fake_read_meta(self) -> dict:
        return {"isProvisioned": state["provisioned"], "indexesVersion": 1}

    async def fake_provision_tenant(*args, **kwargs) -> None:
        state["provisioned"] = True

    monkeypatch.setattr(MetaCollection, "read_tenant_meta", fake_read_meta)
    monkeypatch.setattr(
        core_settings_module, "provision_tenant", fake_provision_tenant
    )

    repo = AsyncMock()
    repo.get_all_core_settings.side_effect = [[], [_core_setting()]]
    repo.create_core_setting.return_value = DecodedCoreSetting.model_validate(
        CONTENT_TOKEN_PAYLOAD
    )
    controller = _controller(repo)
    body = CreateCoreSetting(nickname="tienda-a", token="content-token")

    first = await controller.create_core_setting(body, None)
    second = await controller.create_core_setting(body, None)

    assert first.nickname == "tienda-a"
    assert second.nickname == "tienda-a"
    # El segundo POST no vuelve a sembrar CoreSettings.
    assert repo.create_core_setting.await_count == 1


@pytest.mark.asyncio
async def test_create_reprovisions_an_incomplete_tenant(monkeypatch):
    _patch_token_manager(monkeypatch, CONTENT_TOKEN_PAYLOAD)
    calls = {"provision": 0}

    async def fake_read_meta(self) -> dict:
        return {"isProvisioned": False, "indexesVersion": 0}

    async def fake_provision_tenant(*args, **kwargs) -> None:
        calls["provision"] += 1

    monkeypatch.setattr(MetaCollection, "read_tenant_meta", fake_read_meta)
    monkeypatch.setattr(
        core_settings_module, "provision_tenant", fake_provision_tenant
    )

    repo = AsyncMock()
    repo.get_all_core_settings.return_value = [_core_setting()]
    controller = _controller(repo)
    body = CreateCoreSetting(nickname="tienda-a", token="content-token")

    result = await controller.create_core_setting(body, None)

    assert normalize_nickname(result.nickname) == "tienda-a"
    assert calls["provision"] == 1
    repo.create_core_setting.assert_not_awaited()
