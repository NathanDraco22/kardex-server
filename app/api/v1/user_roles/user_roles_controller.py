from fastapi import HTTPException, status
from kardex.core.role_manager.role_manager import Modules, RoleManager
from kardex.repos.v1.user_roles import (
    CreateUserRole,
    ModulesCatalogResponse,
    UpdateUserRole,
    UserRoleInDb,
    UserRolesRepository,
    UserRolesDataSource,
)

from responses.v1 import ListResponse


class UserRolesController:
    def __init__(self, user_roles_repo: UserRolesRepository) -> None:
        self.user_roles_repo = user_roles_repo

    def get_modules_catalog(self) -> ModulesCatalogResponse:
        return RoleManager.get_modules_catalog()

    async def create_user_role(self, body: CreateUserRole) -> UserRoleInDb:
        clean_name = body.name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre del rol no puede estar vacío",
            )

        existing = await self.user_roles_repo.get_user_role_by_name(clean_name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un rol con el nombre '{clean_name}'",
            )

        payload = CreateUserRole(name=clean_name, access=list(dict.fromkeys(body.access)))
        return await self.user_roles_repo.create_user_role(payload)

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
        if user_role_id == "Admin":
            if body.name is not None and body.name.strip() != "Admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede renombrar el rol 'Admin'",
                )
            if body.access is not None and Modules.ALL not in body.access:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El rol 'Admin' debe mantener el permiso de acceso total",
                )

        if body.name is not None:
            clean_name = body.name.strip()
            if not clean_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre del rol no puede estar vacío",
                )
            existing = await self.user_roles_repo.get_user_role_by_name(
                clean_name, exclude_id=user_role_id
            )
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un rol con el nombre '{clean_name}'",
                )
            body = UpdateUserRole(
                name=clean_name,
                access=list(dict.fromkeys(body.access)) if body.access is not None else None,
            )
        elif body.access is not None:
            body = UpdateUserRole(access=list(dict.fromkeys(body.access)))

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
        if RoleManager.is_default_role(user_role_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los roles predefinidos del sistema no pueden eliminarse",
            )

        assigned_users = await self.user_roles_repo.count_users_with_role(user_role_id)
        if assigned_users > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el rol porque tiene {assigned_users} usuario(s) asignado(s)",
            )

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
