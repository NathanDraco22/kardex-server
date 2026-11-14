from fastapi import APIRouter, BackgroundTasks, Depends
from kardex.repos.v1.core_settings.models.core_setting_model import DecodedCoreSetting
from kardex.repos.v1.core_settings import CreateCoreSetting, UpdateCoreSetting, CoreSettingInDb

from .core_settings_controller import core_settings_controller
from .depends import validate_super_token

core_settings_router = APIRouter(
    tags=["core_settingsV1"],
    dependencies=[Depends(validate_super_token)],
)


@core_settings_router.post("")
async def create_core_setting(
    body: CreateCoreSetting, bg_tasks: BackgroundTasks
) -> DecodedCoreSetting:
    return await core_settings_controller.create_core_setting(body, bg_tasks)


@core_settings_router.get("")
async def get_all_core_settings() -> list[CoreSettingInDb]:
    return await core_settings_controller.get_all_core_settings()


@core_settings_router.get("/{core_setting_id}")
async def get_core_setting_by_id(core_setting_id: str) -> CoreSettingInDb:
    return await core_settings_controller.get_core_setting_by_id(core_setting_id)


@core_settings_router.patch("/{core_setting_nickname}")
async def update_core_setting_by_nickname(
    core_setting_nickname: str,
    body: UpdateCoreSetting,
) -> CoreSettingInDb:
    """Actualiza un tenant.

    ``Authorization`` lleva el ``id_token`` de plataforma (sin nickname) y el
    body lleva el ``content_token`` con el nickname; el nickname del path debe
    coincidir con el del content token.
    """

    return await core_settings_controller.update_core_setting_by_nickname(
        core_setting_nickname, body
    )


@core_settings_router.delete("/{core_setting_id}")
async def delete_core_setting_by_id(
    core_setting_id: str,
    token: str | None = None,
) -> CoreSettingInDb:
    """Elimina un tenant por id.

    ``token`` es el ``content_token`` (query param) con el nickname del tenant;
    el registro debe pertenecer a ese tenant.
    """

    return await core_settings_controller.delete_core_setting_by_id(
        core_setting_id, token
    )
