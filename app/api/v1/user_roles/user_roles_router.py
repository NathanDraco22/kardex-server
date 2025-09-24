from fastapi import APIRouter

from repos.v1.user_roles import CreateUserRole, UpdateUserRole, UserRoleInDb
from responses.v1 import ListResponse

from .user_roles_controller import user_roles_controller


user_roles_router = APIRouter(tags=["user_rolesV1"])


@user_roles_router.post("")
async def create_user_role(body: CreateUserRole) -> UserRoleInDb:
    return await user_roles_controller.create_user_role(body)


@user_roles_router.get("")
async def get_all_user_roles() -> ListResponse[UserRoleInDb]:
    return await user_roles_controller.get_all_user_roles()


@user_roles_router.get("/{user_role_id}")
async def get_user_role_by_id(user_role_id: str) -> UserRoleInDb:
    return await user_roles_controller.get_user_role_by_id(user_role_id)


@user_roles_router.patch("/{user_role_id}")
async def update_user_role_by_id(
    user_role_id: str, body: UpdateUserRole
) -> UserRoleInDb:
    return await user_roles_controller.update_user_role_by_id(user_role_id, body)


@user_roles_router.delete("/{user_role_id}")
async def delete_user_role_by_id(user_role_id: str) -> UserRoleInDb:
    return await user_roles_controller.delete_user_role_by_id(user_role_id)
