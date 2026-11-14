"""Aprovisionamiento de un tenant nuevo.

Idempotente y reintentable: los ``create_default_*`` usan ``*_if_absent`` y el
propietario se verifica por ``username`` (``create_user`` incrementa
``Counters``; un reintento por ``id`` generaria ``0002``).
"""

from kardex.kardex_config import KardexContext, kardexCtx
from kardex.core.default_values import (
    create_default_app_settings,
    create_default_branch,
    create_default_client,
    create_default_expense_categories,
    create_default_integration,
    create_default_roles,
    create_default_unit_scales,
    create_root_user,
)
from kardex.core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from kardex.repos.v1.users import CreateUser, UsersRepository
from kardex.services.mongo_indexes import (
    CURRENT_INDEX_VERSION,
    create_tenant_indexes,
)
from kardex.services.mongo_collections.v1.meta_collection import (
    write_tenant_meta_document,
)
from kardex.tools import BranchesTool, EtagTool, normalize_nickname
from kardex.tools.kardex_exceptions import InvalidTenantNickname


def _validate_nickname(nickname: str) -> str:
    from kardex.tools import is_valid_tenant_nickname

    normalized = normalize_nickname(nickname)
    if not is_valid_tenant_nickname(normalized):
        raise InvalidTenantNickname(
            f"Invalid tenant nickname: {nickname}", nickname=nickname
        )
    return normalized


async def provision_tenant(
    nickname: str,
    establishment_name: str | None = None,
    owner_name: str | None = None,
    run_indexes: bool = True,
) -> None:
    """Crea los datos semilla de un tenant y su ficha ``Meta``.

    ``run_indexes=False`` deja ``Meta.isProvisioned=False`` /
    ``indexesVersion=0`` y delega los indices a
    ``finalize_tenant_indexes`` (``BackgroundTasks``), para no superar el
    timeout de 5 s del Service Manager.
    """

    normalized = _validate_nickname(nickname)
    token = kardexCtx.set(KardexContext(businessNickname=normalized))
    try:
        await create_default_client()
        await create_default_branch(branch_name=establishment_name)
        await create_default_roles()
        await create_root_user()

        if owner_name:
            await _create_owner_if_absent(owner_name)

        await create_default_expense_categories()
        await create_default_unit_scales()
        await create_default_app_settings()
        await create_default_integration()

        await write_tenant_meta_document(
            normalized,
            is_provisioned=False,
            indexes_version=0,
        )

        if run_indexes:
            await finalize_tenant_indexes(normalized)

        await BranchesTool().refresh_current_branches(normalized)
        await EtagTool().update_branches_etags(normalized)
    finally:
        kardexCtx.reset(token)


async def _create_owner_if_absent(owner_name: str) -> None:
    users_repo = UsersRepository.get_instance()
    existing = await users_repo.get_user_by_username(owner_name)

    if existing is not None:
        return

    await users_repo.create_user(
        CreateUser(
            username=owner_name,
            password="12345",
            role="Admin",
            branches=[ORIGIN_BRANCH_ID],
        )
    )


async def finalize_tenant_indexes(nickname: str) -> None:
    """Crea los indices del tenant y cierra ``Meta``.

    Se ejecuta desde ``BackgroundTasks`` con el nickname explicito: no depende
    del contexto del request.
    """

    normalized = _validate_nickname(nickname)
    token = kardexCtx.set(KardexContext(businessNickname=normalized))
    try:
        await create_tenant_indexes(normalized)
        await write_tenant_meta_document(
            normalized,
            is_provisioned=True,
            indexes_version=CURRENT_INDEX_VERSION,
        )
    finally:
        kardexCtx.reset(token)
