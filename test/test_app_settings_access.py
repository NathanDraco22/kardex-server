from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, Request

from app_middleware.depends.settings_access_middleware import (
    require_settings_access,
)
from kardex.repos.v1.users.models.user_model import UserInDbWithRole, UserRole


def _request(user_id: str | None = "u-1") -> Request:
    state = SimpleNamespace()
    if user_id is not None:
        state.auth_user_id = user_id
    return cast(Request, SimpleNamespace(state=state))


def _user(
    *,
    user_id: str = "u-1",
    username: str = "cashier",
    role: str = "Cajero",
    access: list[str] | None = None,
) -> UserInDbWithRole:
    return UserInDbWithRole(
        id=user_id,
        username=username,
        password="",
        role=role,
        branches=["b-1"],
        createdAt=1700000000000,
        userRole=UserRole(name=role, access=access or []),
    )


@pytest.mark.asyncio
async def test_require_settings_access_allows_admin() -> None:
    user = _user(username="root", role="Admin", access=[])
    repo = SimpleNamespace(get_user_by_id=AsyncMock(return_value=user))

    with patch(
        "app_middleware.depends.settings_access_middleware._users_repo", repo
    ):
        await require_settings_access(_request())


@pytest.mark.asyncio
async def test_require_settings_access_allows_settings_module() -> None:
    user = _user(role="Supervisor", access=["settings"])
    repo = SimpleNamespace(get_user_by_id=AsyncMock(return_value=user))

    with patch(
        "app_middleware.depends.settings_access_middleware._users_repo", repo
    ):
        await require_settings_access(_request())


@pytest.mark.asyncio
async def test_require_settings_access_rejects_cashier() -> None:
    user = _user(access=["commercial"])
    repo = SimpleNamespace(get_user_by_id=AsyncMock(return_value=user))

    with patch(
        "app_middleware.depends.settings_access_middleware._users_repo", repo
    ):
        with pytest.raises(HTTPException) as exc:
            await require_settings_access(_request())

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_settings_access_rejects_missing_user() -> None:
    repo = SimpleNamespace(get_user_by_id=AsyncMock(return_value=None))

    with patch(
        "app_middleware.depends.settings_access_middleware._users_repo", repo
    ):
        with pytest.raises(HTTPException) as exc:
            await require_settings_access(_request())

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_settings_access_rejects_missing_identity() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_settings_access(_request(user_id=None))

    assert exc.value.status_code == 401
