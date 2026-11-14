import sys
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.core.tenant import provision_tenant
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    BranchesCollection,
    MetaCollection,
    UsersCollection,
)
from kardex.services.mongo_indexes import get_target_indexes_version
from test.mongo_test_utils import mongo_available

pytestmark = pytest.mark.skipif(
    not mongo_available(),
    reason="MongoDB no disponible: se omite la prueba de aprovisionamiento",
)

TENANT = "mt_test_provision"
OWNER = "owner_mt"


async def _service() -> MongoService:
    service = MongoService()
    if not hasattr(service, "client"):
        await service.init_client()
    return service


async def _drop_database() -> None:
    service = await _service()
    await service.client.drop_database(TENANT)


@pytest.mark.asyncio
async def test_provision_tenant_is_idempotent():
    await _drop_database()

    try:
        await provision_tenant(
            TENANT, establishment_name="Tenant Test", owner_name=OWNER
        )
        await provision_tenant(
            TENANT, establishment_name="Tenant Test", owner_name=OWNER
        )

        users = UsersCollection.get_instance(TENANT)._collection
        owners = await users.count_documents({"username": OWNER})
        roots = await users.count_documents({"id": "root"})

        branches = await BranchesCollection.get_instance(TENANT)._collection.count_documents(
            {}
        )

        meta = await MetaCollection.get_instance(TENANT).read_tenant_meta()

        assert owners == 1
        assert roots == 1
        assert branches == 1

        assert meta is not None
        assert meta["isProvisioned"] is True
        assert meta["indexesVersion"] == get_target_indexes_version()
    finally:
        await _drop_database()
