from fastapi import HTTPException, status

from repos.v1.user_roles import (
    CreateUserRole,
    UpdateUserRole,
    UserRoleInDb,
    UserRolesRepository,
    UserRolesDataSource,
)

from responses.v1 import ListResponse


class UserRolesController:
    def __init__(self, user_roles_repo: UserRolesRepository) -> None:
        self.user_roles_repo = user_roles_repo

    async def create_user_role(self, body: CreateUserRole) -> UserRoleInDb:
        return await self.user_roles_repo.create_user_role(body)

    async def get_all_user_roles(self) -> ListResponse[UserRoleInDb]:
        user_roles = await self.user_roles_repo.get_all_user_roles()
        return ListResponse(count=len(user_roles), data=user_roles)

    async def get_user_role_by_id(self, user_role_id: str) -> UserRoleInDb:
        user_role = await self.user_roles_repo.get_user_role_by_id(user_role_id)
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UserRole not found",
            )
        return user_role

    async def update_user_role_by_id(
        self, user_role_id: str, body: UpdateUserRole
    ) -> UserRoleInDb:
        updated_user_role = await self.user_roles_repo.update_user_role_by_id(
            user_role_id, body
        )
        if updated_user_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UserRole not found",
            )
        return updated_user_role

    async def delete_user_role_by_id(self, user_role_id: str) -> UserRoleInDb:
        deleted_user_role = await self.user_roles_repo.delete_user_role_by_id(
            user_role_id
        )
        if deleted_user_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UserRole not found",
            )
        return deleted_user_role


user_roles_controller = UserRolesController(
    user_roles_repo=UserRolesRepository(
        user_roles_ds=UserRolesDataSource(),
    ),
)
