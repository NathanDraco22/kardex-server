from typing import Any
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from core.security import SysPasswordHasher, TokenManager
from repos.v1.users import UsersRepository, UsersDataSource

from .body import LoginBody
from .responses import LoginResponse


class AuthsController:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def login(self, body: LoginBody) -> LoginResponse:
        user = await self.users_repo.get_user_by_id(body.userId)
        if user is None:
            SysPasswordHasher.verify_password(body.password, "fake_hashed_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not SysPasswordHasher.verify_password(body.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        expiration = datetime.now(tz=timezone.utc) + timedelta(days=1)

        milliseconds = int(expiration.timestamp())

        token = TokenManager.encode_token(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "userRole": user.userRole.model_dump(),
                },
                "exp": milliseconds,
            }
        )

        return LoginResponse(
            user=user,
            accessToken=token,
        )

    async def refresh_token(self, token: str) -> LoginResponse:
        res = TokenManager.decode_token(token)

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid token",
            )

        user = res.get("user")

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        username = user.get("id")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user = await self.users_repo.get_user_by_id(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active",
            )

        expiration = datetime.now(tz=timezone.utc) + timedelta(days=1)

        milliseconds = int(expiration.timestamp())

        token = TokenManager.encode_token(
            {
                "user": {
                    "username": user.username,
                    "userRole": user.userRole.model_dump(),
                },
                "exp": milliseconds,
            }
        )

        return LoginResponse(
            user=user,
            accessToken=token,
        )

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> dict[str, Any]:
        user = await self.users_repo.get_user_by_id(user_id)

        if user is None:
            SysPasswordHasher.verify_password(old_password, "fake_hashed_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not SysPasswordHasher.verify_password(old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        await self.users_repo.change_password(user_id, new_password)

        return {"message": "Password changed successfully"}


auths_controller = AuthsController(
    users_repo=UsersRepository(
        users_ds=UsersDataSource(),
    ),
)
