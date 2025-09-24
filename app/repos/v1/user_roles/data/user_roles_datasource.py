from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import UserRolesCollection


class UserRolesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_user_role(self, user_role: dict[str, Any]) -> dict[str, Any]:
        collection = UserRolesCollection()
        await collection.create_user_role(user_role)
        return user_role

    async def create_user_role_if_absent(
        self,
        user_role_id: str,
        user_role: dict[str, Any],
    ) -> None:
        collection = UserRolesCollection()
        await collection.create_role_if_absent(user_role_id, user_role)

    async def get_all_user_roles(self) -> list[dict[str, Any]]:
        collection = UserRolesCollection()
        return await collection.fetch_all_user_roles()

    async def get_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = UserRolesCollection()
        return await collection.fetch_user_role_by_id(user_role_id)

    async def update_user_role_by_id(
        self, user_role_id: str, user_role: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UserRolesCollection()
        return await collection.update_user_role_by_id(user_role_id, user_role)

    async def delete_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = UserRolesCollection()
        return await collection.delete_user_role_by_id(user_role_id)
