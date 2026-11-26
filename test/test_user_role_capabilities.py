from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.user_roles.user_roles_controller import UserRolesController
from kardex.core.default_values.create_default_roles import create_default_roles
from kardex.core.role_manager.role_manager import RoleManager
from kardex.repos.v1.user_roles.models.user_role_model import (
    CreateUserRole,
    RoleCapabilities,
    UpdateUserRole,
    UserRoleInDb,
)
from kardex.repos.v1.users.models.user_model import UserInDbWithRole


def test_legacy_role_and_user_default_capabilities_to_true():
    legacy_role = {
        "id": "role-1",
        "name": "Vendedor",
        "access": ["commercial", "createInvoice"],
        "createdAt": 1700000000000,
    }
    role = UserRoleInDb.model_validate(legacy_role)
    assert role.capabilities.allowInvoicing is True
    assert role.capabilities.allowCreditInvoicing is True
    assert role.capabilities.showClientCreditDetails is True

    legacy_user = {
        "id": "u-1",
        "username": "vendedor1",
        "password": "secret",
        "role": "role-1",
        "branches": ["b-1"],
        "createdAt": 1700000000000,
        "userRole": {
            "name": "Vendedor",
            "access": ["commercial"],
        },
    }
    user = UserInDbWithRole.model_validate(legacy_user)
    assert user.userRole.capabilities == RoleCapabilities()


def test_create_and_update_role_capabilities_serialization():
    caps = RoleCapabilities(
        allowInvoicing=False,
        allowCreditInvoicing=False,
        showClientCreditDetails=False,
    )
    create_model = CreateUserRole(
        name="Solo Pedidos",
        access=["commercial", "orders"],
        capabilities=caps,
    )
    dumped = create_model.model_dump()
    assert dumped["capabilities"] == {
        "allowInvoicing": False,
        "allowCreditInvoicing": False,
        "showClientCreditDetails": False,
    }

    update_model = UpdateUserRole(capabilities=caps)
    assert update_model.model_dump(exclude_unset=True) == {
        "capabilities": {
            "allowInvoicing": False,
            "allowCreditInvoicing": False,
            "showClientCreditDetails": False,
        }
    }


@pytest.mark.asyncio
async def test_controller_protects_admin_capabilities_and_preserves_on_update():
    repo = MagicMock()
    repo.get_user_role_by_name = AsyncMock(return_value=None)
    repo.update_user_role_by_id = AsyncMock(
        return_value=UserRoleInDb(
            id="role-2",
            name="Cajero Contado",
            access=["commercial"],
            capabilities=RoleCapabilities(allowCreditInvoicing=False),
            createdAt=1700000000000,
        )
    )
    controller = UserRolesController(user_roles_repo=repo)

    with pytest.raises(HTTPException) as exc_info:
        await controller.update_user_role_by_id(
            "Admin",
            UpdateUserRole(
                capabilities=RoleCapabilities(allowCreditInvoicing=False),
            ),
        )
    assert exc_info.value.status_code == 400

    await controller.update_user_role_by_id(
        "role-2",
        UpdateUserRole(
            name="Cajero Contado",
            access=["commercial", "commercial"],
            capabilities=RoleCapabilities(allowCreditInvoicing=False),
        ),
    )
    _, passed_body = repo.update_user_role_by_id.call_args.args
    assert passed_body.name == "Cajero Contado"
    assert passed_body.access == ["commercial"]
    assert passed_body.capabilities == RoleCapabilities(allowCreditInvoicing=False)


@pytest.mark.asyncio
async def test_default_cajero_role_disables_credit_invoicing(monkeypatch):
    assert RoleManager.is_default_role("Cajero") is True
    cajero = next(
        (r for r in RoleManager.get_default_roles() if r.name == "Cajero"),
        None,
    )
    assert cajero is not None
    assert cajero.capabilities == RoleCapabilities(
        allowInvoicing=True,
        allowCreditInvoicing=False,
        showClientCreditDetails=True,
    )

    collection = MagicMock()
    collection.create_role_if_absent = AsyncMock()
    collection.fetch_user_role_by_id = AsyncMock(return_value=None)

    from kardex.services.mongo_collections.v1 import UserRolesCollection

    monkeypatch.setattr(
        UserRolesCollection,
        "get_instance",
        classmethod(lambda cls: collection),
    )

    await create_default_roles()

    cajero_calls = [
        call.args
        for call in collection.create_role_if_absent.call_args_list
        if call.args[0] == "Cajero"
    ]
    assert len(cajero_calls) == 1
    assert cajero_calls[0][1]["capabilities"] == {
        "allowInvoicing": True,
        "allowCreditInvoicing": False,
        "showClientCreditDetails": True,
    }
