from fastapi import APIRouter
from typing import Any

from .auths_controller import auths_controller
from .body import LoginBody, RefreshTokenBody

auths_router = APIRouter(tags=["authsV1"])


@auths_router.post("/login")
async def create_auth(body: LoginBody) -> Any:
    return await auths_controller.login(body)


@auths_router.post("/refresh-token")
async def refresh_token(body: RefreshTokenBody) -> Any:
    return await auths_controller.refresh_token(body.token)
