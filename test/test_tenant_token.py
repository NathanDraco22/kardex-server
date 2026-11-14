import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.api.v1.auths.auths_controller import AuthsController
from app_middleware.depends.auth_middleware import auth_middleware
from kardex.core.security import TokenManager
from kardex.kardex_config import KardexContext, kardexCtx
from kardex.repos.v1.users import UserInDbWithRole
from kardex.repos.v1.users.models.user_model import UserRole


def _make_token(tenant: str | None, user_id: str = "0001") -> str:
    expiration = datetime.now(tz=timezone.utc) + timedelta(days=1)
    payload: dict = {
        "user": {
            "id": user_id,
            "username": "propietario",
            "userRole": {"name": "Admin", "access": []},
        },
        "exp": int(expiration.timestamp()),
    }
    if tenant is not None:
        payload["tenant"] = tenant
    return TokenManager.encode_token(payload)


def _make_request(token: str) -> Request:
    return Request(
        {
            "type": "http",
            "headers": [
                (b"authorization", f"Bearer {token}".encode()),
            ],
        }
    )


def _user() -> UserInDbWithRole:
    return UserInDbWithRole(
        id="0001",
        username="propietario",
        password="hashed",
        role="Admin",
        createdAt=1700000000000,
        userRole=UserRole(name="Admin", access=[]),
    )


def _controller(user: UserInDbWithRole | None) -> AuthsController:
    users_repo = AsyncMock()
    users_repo.get_user_by_id.return_value = user
    return AuthsController(
        users_repo=users_repo,
        core_settings_repo=AsyncMock(),
    )


def test_auth_middleware_accepts_matching_tenant(monkeypatch):
    monkeypatch.setattr(
        "kardex.tools.users_tool.UsersTool.get_inactive_user_by_id",
        lambda self, user_id: None,
    )
    token = kardexCtx.set(KardexContext(businessNickname="tienda-a"))
    try:
        auth_middleware(_make_request(_make_token("tienda-a")))
    finally:
        kardexCtx.reset(token)


def test_auth_middleware_rejects_cross_tenant_token(monkeypatch):
    monkeypatch.setattr(
        "kardex.tools.users_tool.UsersTool.get_inactive_user_by_id",
        lambda self, user_id: None,
    )
    token = kardexCtx.set(KardexContext(businessNickname="tienda-b"))
    try:
        with pytest.raises(HTTPException) as exc:
            auth_middleware(_make_request(_make_token("tienda-a")))
    finally:
        kardexCtx.reset(token)

    assert exc.value.status_code == 403


def test_auth_middleware_rejects_token_without_tenant_claim(monkeypatch):
    monkeypatch.setattr(
        "kardex.tools.users_tool.UsersTool.get_inactive_user_by_id",
        lambda self, user_id: None,
    )
    token = kardexCtx.set(KardexContext(businessNickname="tienda-a"))
    try:
        with pytest.raises(HTTPException) as exc:
            auth_middleware(_make_request(_make_token(None)))
    finally:
        kardexCtx.reset(token)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token_rejects_cross_tenant_token():
    controller = _controller(_user())
    token = kardexCtx.set(KardexContext(businessNickname="tienda-b"))
    try:
        with pytest.raises(HTTPException) as exc:
            await controller.refresh_token(_make_token("tienda-a"))
    finally:
        kardexCtx.reset(token)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token_preserves_tenant_claim():
    controller = _controller(_user())
    token = kardexCtx.set(KardexContext(businessNickname="tienda-a"))
    try:
        response = await controller.refresh_token(_make_token("tienda-a"))
    finally:
        kardexCtx.reset(token)

    decoded = TokenManager.decode_token(response.accessToken)
    assert decoded is not None
    assert decoded["tenant"] == "tienda-a"
