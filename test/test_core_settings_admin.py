import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.api.v1.core_settings.core_settings_controller import CoreSettingsController
from kardex.core.security import TokenManager
from kardex.repos.v1.core_settings import CreateCoreSetting


def _controller() -> CoreSettingsController:
    return CoreSettingsController(
        core_settings_repo=AsyncMock(),
        branches_repo=AsyncMock(),
        users_repo=AsyncMock(),
    )


def test_patch_validates_path_against_token_nickname():
    controller = _controller()

    with pytest.raises(HTTPException) as exc:
        controller._assert_path_matches_token(
            "tienda-b", {"nickname": "tienda-a"}
        )

    assert exc.value.status_code == 403


def test_patch_normalizes_nicknames():
    controller = _controller()

    nickname = controller._assert_path_matches_token(
        "  TiendaA ", {"nickname": "tiendaa"}
    )

    assert nickname == "tiendaa"


@pytest.mark.asyncio
async def test_create_rejects_body_nickname_different_from_token(monkeypatch):
    monkeypatch.setattr(
        TokenManager,
        "super_token_verify",
        staticmethod(lambda token: {"nickname": "tienda-a"}),
    )
    controller = _controller()
    body = CreateCoreSetting(nickname="tienda-b", token="super-token")

    with pytest.raises(HTTPException) as exc:
        await controller.create_core_setting(body)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_rejects_invalid_nickname(monkeypatch):
    monkeypatch.setattr(
        TokenManager,
        "super_token_verify",
        staticmethod(lambda token: {"nickname": "admin"}),
    )
    controller = _controller()
    body = CreateCoreSetting(nickname="admin", token="super-token")

    with pytest.raises(HTTPException) as exc:
        await controller.create_core_setting(body)

    assert exc.value.status_code == 400
