from fastapi import BackgroundTasks, HTTPException, status

from kardex.core.security import TokenManager
from kardex.core.tenant import finalize_tenant_indexes, provision_tenant
from kardex.kardex_config import KardexContext, kardexCtx
from kardex.services.mongo_collections.v1 import MetaCollection
from kardex.tools import (
    is_valid_tenant_nickname,
    normalize_nickname,
    run_with_tenant_context,
)

from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.users import UsersRepository, UsersDataSource
from kardex.repos.v1.core_settings import (
    CreateCoreSetting,
    UpdateCoreSetting,
    CoreSettingInDb,
    DecodedCoreSetting,
    CoreSettingsRepository,
    CoreSettingsDataSource,
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

    @staticmethod
    def _token_nickname(token_payload: dict | None) -> str:
        nickname = normalize_nickname(str((token_payload or {}).get("nickname", "")))

        if not nickname:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch",
            )

        return nickname

    def _assert_path_matches_token(
        self, path_nickname: str, token_payload: dict | None
    ) -> str:
        nickname = normalize_nickname(path_nickname)
        token_nickname = self._token_nickname(token_payload)

        if nickname != token_nickname:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch",
            )

        return nickname

    @staticmethod
    def _decode_content_token(token: str | None) -> dict:
        """Decodifica el token de contenido (Ed25519) que lleva el nickname.

        El Service Manager autentica el request con un ``id_token``
        (``sub``/``origin``/``exp``, sin nickname) en ``Authorization`` y manda
        la configuracion del negocio en un ``content_token`` aparte.
        """

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing content token",
            )

        decoded = TokenManager.super_token_verify(token)

        if decoded is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return decoded

    @staticmethod
    def _assert_header_matches(nickname: str) -> None:
        """Si el request trae header de tenant, debe coincidir con el token."""

        header_nickname = normalize_nickname(kardexCtx.get().businessNickname)

        if header_nickname and header_nickname != nickname:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch",
            )

    async def create_core_setting(
        self,
        body: CreateCoreSetting,
        bg_tasks: BackgroundTasks | None = None,
    ) -> DecodedCoreSetting:
        decoded = TokenManager.super_token_verify(body.token)

        if decoded is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        nickname = normalize_nickname(body.nickname)
        token_nickname = self._token_nickname(decoded)

        if not nickname or nickname != token_nickname:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch",
            )

        if not is_valid_tenant_nickname(nickname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant nickname",
            )

        # El contexto debe fijarse antes de cualquier lectura de CoreSettings:
        # la DB destino es la del nickname, no la del header.
        token_ctx = kardexCtx.set(KardexContext(businessNickname=nickname))
        try:
            settings = await self.get_all_core_settings()
            meta = await MetaCollection.get_instance().read_tenant_meta()
            is_provisioned = bool(meta and meta.get("isProvisioned") is True)

            if settings and is_provisioned:
                # Idempotente: el Service Manager reintenta si no recibio el 200
                # y el tenant ya esta completo. No se re-aprovisiona.
                repeated = DecodedCoreSetting.model_validate(decoded)
                return repeated.model_copy(update={"nickname": nickname})

            if settings:
                # Reintento tras un aprovisionamiento incompleto: no se
                # duplica CoreSettings y los defaults son ``*_if_absent``.
                res: DecodedCoreSetting | None = DecodedCoreSetting.model_validate(
                    decoded
                )
            else:
                normalized_body = body.model_copy(update={"nickname": nickname})
                res = await self.core_settings_repo.create_core_setting(
                    normalized_body
                )

            if res is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CoreSetting not found",
                )

            res = res.model_copy(update={"nickname": nickname})

            await provision_tenant(
                nickname,
                establishment_name=res.name,
                owner_name=res.ownerName,
                run_indexes=False,
            )

            if bg_tasks is not None:
                bg_tasks.add_task(
                    run_with_tenant_context,
                    nickname,
                    finalize_tenant_indexes,
                    nickname,
                )

            return res
        finally:
            kardexCtx.reset(token_ctx)

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
        self,
        core_setting_id: str,
        body: UpdateCoreSetting,
    ) -> CoreSettingInDb:
        decoded = self._decode_content_token(body.token)
        nickname = self._assert_path_matches_token(core_setting_id, decoded)
        self._assert_header_matches(nickname)

        token_ctx = kardexCtx.set(KardexContext(businessNickname=nickname))
        try:
            updated_core_setting = (
                await self.core_settings_repo.update_core_setting_by_nickname(
                    nickname, body
                )
            )
        finally:
            kardexCtx.reset(token_ctx)

        if updated_core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return updated_core_setting

    async def delete_core_setting_by_id(
        self,
        core_setting_id: str,
        content_token: str | None = None,
    ) -> CoreSettingInDb:
        decoded = self._decode_content_token(content_token)
        nickname = self._token_nickname(decoded)
        self._assert_header_matches(nickname)

        token_ctx = kardexCtx.set(KardexContext(businessNickname=nickname))
        try:
            existing = await self.core_settings_repo.get_core_setting_by_id(
                core_setting_id
            )

            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CoreSetting not found",
                )

            # El path es un id, no un nickname: se valida el dueno del registro
            # contra el content token.
            if normalize_nickname(existing.nickname) != nickname:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant mismatch",
                )

            deleted_core_setting = (
                await self.core_settings_repo.delete_core_setting_by_id(
                    core_setting_id
                )
            )
        finally:
            kardexCtx.reset(token_ctx)

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
