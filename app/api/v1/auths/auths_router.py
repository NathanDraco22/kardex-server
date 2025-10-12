from fastapi import APIRouter

from .auths_controller import auths_controller
from .body import LoginBody, RefreshTokenBody, ChangePasswordBody
from .responses import LoginResponse

auths_router = APIRouter(tags=["authsV1"])


@auths_router.post("/login")
async def create_auth(body: LoginBody) -> LoginResponse:
    return await auths_controller.login(body)


@auths_router.post("/refresh-token")
async def refresh_token(body: RefreshTokenBody) -> LoginResponse:
    return await auths_controller.refresh_token(body.token)


@auths_router.post("/change-password")
async def change_password(body: ChangePasswordBody) -> dict:
    return await auths_controller.change_password(
        body.userId,
        body.oldPassword,
        body.newPassword,
    )
