import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.api.v1.user_roles.user_roles_controller import UserRolesController
from kardex.core.role_manager.role_manager import CommercialSubModules, Modules, RoleManager
from kardex.repos.v1.user_roles import CreateUserRole, UpdateUserRole, UserRoleInDb


def _make_role(role_id: str, name: str, access: list[str], is_default: bool = False) -> UserRoleInDb:
    return UserRoleInDb(
        id=role_id,
        name=name,
        access=access,
        createdAt=1700000000000,
        isDefault=is_default,
    )


def test_modules_catalog_contains_expected_modules_and_commercial_submodules():
    catalog = RoleManager.get_modules_catalog()
    assert catalog.allAccessKey == Modules.ALL

    module_keys = {m.key for m in catalog.modules}
    assert {
        Modules.CLIENTS,
        Modules.SUPPLIERS,
        Modules.PRODUCTS,
        Modules.COMMERCIAL,
        Modules.PENDING_INVOICES,
        Modules.INVENTORY,
        Modules.EXPENSES,
        Modules.FINANCE,
        Modules.ADVANCED_TOOLS,
        Modules.SETTINGS,
    }.issubset(module_keys)

    commercial = next(m for m in catalog.modules if m.key == Modules.COMMERCIAL)
    sub_keys = {s.key for s in commercial.submodules}
    assert CommercialSubModules.CREATE_INVOICE in sub_keys
    assert CommercialSubModules.CREDIT_NOTE_HISTORY in sub_keys
    assert len(commercial.submodules) == 11


@pytest.mark.asyncio
async def test_create_user_role_rejects_empty_or_duplicate_name():
    repo = AsyncMock()
    repo.get_user_role_by_name.return_value = None
    repo.create_user_role.return_value = _make_role("uuid-1", "Cajero", ["commercial", "createInvoice"])

    controller = UserRolesController(user_roles_repo=repo)

    with pytest.raises(HTTPException) as exc:
        await controller.create_user_role(CreateUserRole(name="   ", access=[]))
    assert exc.value.status_code == 400

    created = await controller.create_user_role(
        CreateUserRole(name=" Cajero ", access=["commercial", "createInvoice", "commercial"])
    )
    assert created.name == "Cajero"
    repo.create_user_role.assert_awaited_once()
    sent_payload = repo.create_user_role.call_args.args[0]
    assert sent_payload.name == "Cajero"
    assert sent_payload.access == ["commercial", "createInvoice"]

    repo.get_user_role_by_name.return_value = _make_role("uuid-1", "Cajero", [])
    with pytest.raises(HTTPException) as dup_exc:
        await controller.create_user_role(CreateUserRole(name="cajero", access=[]))
    assert dup_exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_admin_role_protects_name_and_all_access():
    repo = AsyncMock()
    controller = UserRolesController(user_roles_repo=repo)

    with pytest.raises(HTTPException) as rename_exc:
        await controller.update_user_role_by_id("Admin", UpdateUserRole(name="SuperAdmin"))
    assert rename_exc.value.status_code == 400

    with pytest.raises(HTTPException) as access_exc:
        await controller.update_user_role_by_id("Admin", UpdateUserRole(access=["clients"]))
    assert access_exc.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_role_blocks_default_roles_and_assigned_roles():
    repo = AsyncMock()
    controller = UserRolesController(user_roles_repo=repo)

    for default_id in ["Admin", "Pre-Venta", "Vendedor", "Operador", "Supervisor"]:
        with pytest.raises(HTTPException) as exc:
            await controller.delete_user_role_by_id(default_id)
        assert exc.value.status_code == 400

    repo.count_users_with_role.return_value = 3
    with pytest.raises(HTTPException) as assigned_exc:
        await controller.delete_user_role_by_id("custom-role-1")
    assert assigned_exc.value.status_code == 400

    repo.count_users_with_role.return_value = 0
    repo.delete_user_role_by_id.return_value = _make_role("custom-role-1", "Cajero", [])
    deleted = await controller.delete_user_role_by_id("custom-role-1")
    assert deleted.id == "custom-role-1"
