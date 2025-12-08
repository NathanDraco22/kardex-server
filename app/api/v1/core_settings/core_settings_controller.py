from fastapi import HTTPException, status

from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.users import UsersRepository, UsersDataSource, CreateUser
from repos.v1.core_settings import (
    CreateCoreSetting,
    UpdateCoreSetting,
    CoreSettingInDb,
    DecodedCoreSetting,
    CoreSettingsRepository,
    CoreSettingsDataSource,
)


from core.default_values import (
    create_default_client,
    create_default_branch,
)


class CoreSettingsController:
    def __init__(
        self,
        core_settings_repo: CoreSettingsRepository,
        branches_repo: BranchesRepository,
        users_repo: UsersRepository,
    ) -> None:
        self.core_settings_repo = core_settings_repo
        self.branches_repo = branches_repo
        self.users_repo = users_repo

    async def create_core_setting(self, body: CreateCoreSetting) -> DecodedCoreSetting:
        settings = await self.get_all_core_settings()

        if len(settings) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CoreSetting already exists",
            )

        res = await self.core_settings_repo.create_core_setting(body)

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )

        await create_default_client()
        await create_default_branch(branch_name=res.name)

        origin_user = CreateUser(username=res.ownerName, password="12345", role="Admin")

        await self.users_repo.create_user(origin_user)

        return res

    async def get_all_core_settings(self) -> list[CoreSettingInDb]:
        core_settings = await self.core_settings_repo.get_all_core_settings()
        return core_settings

    async def get_core_setting_by_id(self, core_setting_id: str) -> CoreSettingInDb:
        core_setting = await self.core_settings_repo.get_core_setting_by_id(
            core_setting_id
        )
        if core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return core_setting

    async def update_core_setting_by_nickname(
        self, core_setting_id: str, body: UpdateCoreSetting
    ) -> CoreSettingInDb:
        updated_core_setting = (
            await self.core_settings_repo.update_core_setting_by_nickname(
                core_setting_id, body
            )
        )
        if updated_core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return updated_core_setting

    async def delete_core_setting_by_id(self, core_setting_id: str) -> CoreSettingInDb:
        deleted_core_setting = await self.core_settings_repo.delete_core_setting_by_id(
            core_setting_id
        )
        if deleted_core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return deleted_core_setting


core_settings_controller = CoreSettingsController(
    core_settings_repo=CoreSettingsRepository(
        core_settings_ds=CoreSettingsDataSource(),
    ),
    branches_repo=BranchesRepository(
        branches_ds=BranchesDataSource(),
    ),
    users_repo=UsersRepository(
        users_ds=UsersDataSource(),
    ),
)
